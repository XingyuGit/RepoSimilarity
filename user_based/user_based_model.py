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

    def save(self, directory=None):
        if directory is None:
            directory = self.directory

        pickle.dump(self.id2repo, open('%s/id2repo' % directory, 'w'))
        self.dictionary.save('%s/users.dict' % directory)

        corpora.MmCorpus.serialize('%s/corpus_bow.mm' % directory, self.corpus)
        corpora.MmCorpus.serialize('%s/corpus_tfidf.mm' % directory, self.corpus_tfidf)
        corpora.MmCorpus.serialize('%s/corpus_lda.mm' % directory, self.corpus_lda)

        self.tfidf.save('%s/tfidf.model' % directory)
        self.lda.save('%s/lda.model' % directory)

        self.sim_tfidf_index.save('%s/tfidf.index' % directory)
        self.sim_lda_index.save('%s/lda.index' % directory)

    def load(self, directory=None):
        if directory is None:
            directory = self.directory

        self.id2repo = pickle.load(open('%s/id2repo' % directory, 'r'))
        self.dictionary = corpora.Dictionary.load('%s/users.dict' % directory)
        self.corpus = corpora.MmCorpus('%s/corpus_bow.mm' % directory)
        self.corpus_tfidf = corpora.MmCorpus('%s/corpus_tfidf.mm' % directory)
        self.corpus_lda = corpora.MmCorpus('%s/corpus_lda.mm' % directory)
        self.tfidf = models.TfidfModel.load('%s/tfidf.model' % directory)
        self.lda = models.LdaMulticore.load('%s/lda.model' % directory)
        self.sim_tfidf_index = similarities.Similarity.load('%s/tfidf.index' % directory)
        self.sim_lda_index = similarities.Similarity.load('%s/lda.index' % directory)

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

        return [(self.id2repo[id], cosine) for id, cosine in sims]

    def set_num_best(self, num_best):
        self.num_best = num_best
        self.sim_tfidf_index.num_best = num_best
        self.sim_lda_index.num_best = num_best

first_time = False
model = RepoModel()
if not first_time:
    model.load()

cache = {}
def find_similar_repos(repo_name, type="lda", num_best=100):
    if cache.has_key((repo_name, type, num_best)):
        return cache[(repo_name, type, num_best)]
    model.set_num_best(num_best)
    sims = model.query(repo_name, type)
    cache[(repo_name, type, num_best)] = sims
    return sims

if __name__ == '__main__':
    if first_time:
        model.init()
        model.save()
    else:
        model.load()
    model.set_num_best(100)
    sims = model.query("jashkenas/backbone")
    print sims
