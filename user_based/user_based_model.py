import logging
import redis
from gensim import corpora, models, similarities
import itertools
import os
import pickle
import math

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

r = redis.StrictRedis(host='localhost', port=6379, db=0)

def ensure_directory(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)
    return directory

class RepoModel(object):

    num_topics = 100
    # num_stars_upper_bound = 100
    num_repos_upper_bound = 2000000

    def __init__(self, directory='gensim'):
        self.i = 0
        self.id2repo = {}
        self.directory = ensure_directory(directory)
        self.num_best = 100

    def iterator(self):
        for key in itertools.islice(r.scan_iter('repo:*'), 0, self.num_repos_upper_bound):
            self.id2repo[self.i] = key[5:]
            self.i += 1
            yield r.smembers(key)

    def init(self):
        # compute dictionary
        self.dictionary = corpora.Dictionary(self.iterator())
        # remove gaps in id sequence after words that were removed
        self.dictionary.compactify()
        # remove extreme words
        self.dictionary.filter_extremes(no_below=5, no_above=0.1, keep_n=None)
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
        pickle.dump(self.id2repo, open('%s/id2repo' % self.directory, 'w'))
        self.dictionary.save('%s/users.dict' % self.directory)

        corpora.MmCorpus.serialize('%s/corpus_bow.mm' % self.directory, self.corpus)
        corpora.MmCorpus.serialize('%s/corpus_tfidf.mm' % self.directory, self.corpus_tfidf)
        corpora.MmCorpus.serialize('%s/corpus_lda.mm' % self.directory, self.corpus_lda)

        self.tfidf.save('%s/tfidf.model' % self.directory)
        self.lda.save('%s/lda.model' % self.directory)

        self.sim_tfidf_index.save('%s/tfidf.index' % self.directory)
        self.sim_lda_index.save('%s/lda.index' % self.directory)

    def load(self):
        self.id2repo = pickle.load(open('%s/id2repo' % self.directory, 'r'))
        self.dictionary = corpora.Dictionary.load('%s/users.dict' % self.directory)
        self.corpus = corpora.MmCorpus('%s/corpus_bow.mm' % self.directory)
        self.corpus_tfidf = corpora.MmCorpus('%s/corpus_tfidf.mm' % self.directory)
        self.corpus_lda = corpora.MmCorpus('%s/corpus_lda.mm' % self.directory)
        self.tfidf = models.TfidfModel.load('%s/tfidf.model' % self.directory)
        self.lda = models.LdaMulticore.load('%s/lda.model' % self.directory)
        self.sim_tfidf_index = similarities.Similarity.load('%s/tfidf.index' % self.directory)
        self.sim_lda_index = similarities.Similarity.load('%s/lda.index' % self.directory)

    def query(self, repo, type="lda"):
        users = r.smembers("repo:" + repo)
        vec_bow = self.dictionary.doc2bow(users)

        if type == "lda":
            vec_lda = self.lda[vec_bow]
            sims = self.sim_lda_index[vec_lda]
        elif type == "tfidf":
            vec_tfidf = self.tfidf[vec_bow]
            sims = self.sim_tfidf_index[vec_tfidf]
        else:
            return None

        return dict(sims)

    def set_num_best(self, num_best):
        self.num_best = num_best
        self.sim_tfidf_index.num_best = num_best
        self.sim_lda_index.num_best = num_best


first_time = False
model = RepoModel()
if not first_time:
    model.load()

def find_similar_repos(repo_name, type="lda"):
    model.set_num_best(100)
    sims = model.query(repo_name, type)
    return sims

if __name__ == '__main__':
    if first_time:
        model.init()
        model.save()
    model.set_num_best(100)
    sims = model.query("jashkenas/backbone", "tfidf")
    print sims
