import logging
import pymongo
from gensim import corpora, models, similarities
import itertools
import os
from global_import import stars

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
    # word_frequency_upper_bound = 1000
    num_repos_upper_bound = 2000000

    def __init__(self, directory='gensim_text'):
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
        self.dictionary.filter_extremes(no_below=10, no_above=0.1, keep_n=None)
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

    def save(self, directory=None):
        if directory is None:
            directory = self.directory

        pickle.dump(self.id2doc, open('%s/id2doc' % directory, 'w'))
        self.dictionary.save('%s/words.dict' % directory)

        corpora.MmCorpus.serialize('%s/corpus_bow.mm' % directory, self.corpus)
        corpora.MmCorpus.serialize('%s/corpus_tfidf.mm' % directory, self.corpus_tfidf)
        corpora.MmCorpus.serialize('%s/corpus_lda.mm' % directory, self.corpus_lda)

        self.tfidf.save('%s/tfidf.model' % directory)
        self.lda.save('%s/lda.model' % directory)

        self.recreate_index(directory)

    def recreate_index(self, directory=None):
        if directory is None:
            directory = self.directory

        # compute_similarity_index
        self.sim_tfidf_index = similarities.Similarity('%s/tfidf.shard' % directory,
                        self.corpus_tfidf, len(self.dictionary), chunksize=256, shardsize=131072)
        self.sim_lda_index = similarities.Similarity('%s/lda.shard' % directory,
                        self.corpus_lda, self.lda.num_topics, chunksize=256, shardsize=131072)

        self.sim_tfidf_index.save('%s/tfidf.index' % directory)
        self.sim_lda_index.save('%s/lda.index' % directory)


    def load(self, directory=None):
        if directory is None:
            directory = self.directory
            
        self.id2doc = pickle.load(open('%s/id2doc' % directory, 'r'))
        self.dictionary = corpora.Dictionary.load('%s/words.dict' % directory)
        self.corpus = corpora.MmCorpus('%s/corpus_bow.mm' % directory)
        self.corpus_tfidf = corpora.MmCorpus('%s/corpus_tfidf.mm' % directory)
        self.corpus_lda = corpora.MmCorpus('%s/corpus_lda.mm' % directory)
        self.tfidf = models.TfidfModel.load('%s/tfidf.model' % directory)
        self.lda = models.LdaMulticore.load('%s/lda.model' % directory)
        self.sim_tfidf_index = similarities.Similarity.load('%s/tfidf.index' % directory)
        self.sim_lda_index = similarities.Similarity.load('%s/lda.index' % directory)

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
            return sorted([(self.id2doc[id], cosine) for id, cosine in sims],
                          key=lambda item: -item[1])

    def set_num_best(self, num_best):
        self.num_best = num_best
        self.sim_tfidf_index.num_best = num_best
        self.sim_lda_index.num_best = num_best



first_time = False
model = TextModel()
if not first_time:
    model.load()

cache = {}
def find_similar_repos(repo_name, type="lda", num_best=100):
    if cache.has_key((repo_name, type, num_best)):
        return cache[(repo_name, type, num_best)]
    sims = model.query(repo_name, type)
    sims = [(name, score) for (name, score) in sims if stars.get(name, 0) >= 30]
    cache[(repo_name, type, num_best)] = sims
    return sims[:num_best]

if __name__ == '__main__':
    if first_time:
        model.init()
        model.save()
    else:
        model.load()
    sims = model.query("jashkenas/backbone")
    sims = [(name, score) for (name, score) in sims if stars.get(name, 0) >= 30]
    print sims[:100]

    # model.lda.print_topics()
    # print model.lda.num_topics