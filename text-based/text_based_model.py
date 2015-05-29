import logging
import pymongo
from gensim import corpora, models, similarities
import itertools
import os
import pickle

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

client = pymongo.MongoClient()
db = client.github
repos = db.repos

stoplist = set([line.strip('\n').strip() for line in open('stopwords.txt')])

def ensure_directory(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)
    return directory

class TextModel(object):

    num_topics = 100
    word_frequency_upper_bound = 500
    num_repos_upper_bound = 2000000

    def __init__(self, directory='gensim'):
        self.i = 0
        self.id2doc = {}
        self.directory = ensure_directory(directory)
        self.num_best = None

    def iterator(self):
        for repo in itertools.islice(repos.find(), 0, self.num_repos_upper_bound):
            # join all content in each readme
            words = ' '.join([p['content'] for p in repo['readme']]).split()
            # add description
            words += repo['description'].split()
            # filter words that are too short
            words = [word for word in words if len(word) >= 3]
            # one document at a time
            self.id2doc[self.i] = repo['full_name']
            self.i += 1
            yield words

    def init(self):
        self.dictionary = corpora.Dictionary(self.iterator())
        stop_ids = [self.dictionary.token2id[stopword] for stopword in stoplist
                    if stopword in self.dictionary.token2id]
        # remove stop words and words that appear very few
        self.dictionary.filter_tokens(stop_ids)
        # remove gaps in id sequence after words that were removed
        self.dictionary.compactify()
        # remove extreme words
        self.dictionary.filter_extremes(no_below=5,
                                        no_above=float(self.word_frequency_upper_bound)/len(self.dictionary),
                                        keep_n=None)
        # compute vectors
        self.corpus = [self.dictionary.doc2bow(words) for words in self.iterator()]

        # compute_tfidf
        self.tfidf = models.TfidfModel(self.corpus)
        self.corpus_tfidf = self.tfidf[self.corpus]

        # compute lda
        self.lda = models.LdaMulticore(self.corpus, id2word=self.dictionary, workers=3,
                                       num_topics=self.num_topics, chunksize=10000)
        self.corpus_lda = self.lda[self.corpus]

        # compute_similarity_index
        self.sim_tfidf_index = similarities.Similarity('%s/tfidf.shard' % self.directory,
                        self.corpus_tfidf, len(self.dictionary), chunksize=256, shardsize=131072)
        self.sim_lda_index = similarities.Similarity('%s/lda.shard' % self.directory,
                        self.corpus_lda, self.lda.num_topics, chunksize=256, shardsize=131072)

    def save(self):
        pickle.dump(self.id2doc, open('%s/id2doc' % self.directory, 'w'))
        self.dictionary.save('%s/words.dict' % self.directory)

        corpora.MmCorpus.serialize('%s/corpus_bow.mm' % self.directory, self.corpus)
        corpora.MmCorpus.serialize('%s/corpus_tfidf.mm' % self.directory, self.corpus_tfidf)
        corpora.MmCorpus.serialize('%s/corpus_lda.mm' % self.directory, self.corpus_lda)

        self.tfidf.save('%s/tfidf.model' % self.directory)
        self.lda.save('%s/lda.model' % self.directory)

        self.sim_tfidf_index.save('%s/tfidf.index' % self.directory)
        self.sim_lda_index.save('%s/lda.index' % self.directory)

    def load(self):
        self.id2doc = pickle.load(open('%s/id2doc' % self.directory, 'r'))
        self.dictionary = corpora.Dictionary.load('%s/words.dict' % self.directory)
        self.corpus = corpora.MmCorpus('%s/corpus_bow.mm' % self.directory)
        self.corpus_tfidf = corpora.MmCorpus('%s/corpus_tfidf.mm' % self.directory)
        self.corpus_lda = corpora.MmCorpus('%s/corpus_lda.mm' % self.directory)
        self.tfidf = models.TfidfModel.load('%s/tfidf.model' % self.directory)
        self.lda = models.LdaMulticore.load('%s/lda.model' % self.directory)
        self.sim_tfidf_index = similarities.Similarity.load('%s/tfidf.index' % self.directory)
        self.sim_lda_index = similarities.Similarity.load('%s/lda.index' % self.directory)

    def query(self, repo_name, type="lda"):
        repo = repos.find_one({'full_name': repo_name})
        words = ' '.join([p['content'] for p in repo['readme']]).split()
        # add description
        words += repo['description'].split()
        # filter words that are too short
        words = [word for word in words if len(word) >= 3]
        vec_bow = self.dictionary.doc2bow(words)

        if type == "lda":
            vec_lda = self.lda[vec_bow]
            sims = self.sim_lda_index[vec_lda]
        elif type == "tfidf":
            vec_tfidf = self.tfidf[vec_bow]
            sims = self.sim_tfidf_index[vec_tfidf]
        else:
            return None

        if self.num_best is None:
            return [(self.id2doc[id], cosine) for id, cosine in
                sorted(enumerate(sims), key=lambda item: -item[1]) if cosine > 0]
        else:
            return [(self.id2doc[id], cosine) for id, cosine in sims]

    def set_num_best(self, num_best):
        self.num_best = num_best
        self.sim_tfidf_index.num_best = num_best
        self.sim_lda_index.num_best = num_best

if __name__ == '__main__':
    model = TextModel()
    first_time = False
    if first_time:
        model.init()
        model.save()
    else:
        model.load()
    model.set_num_best(100)
    sims = model.query("andymccurdy/redis-py")
    print sims