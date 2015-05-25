import logging
import pymongo
from gensim import corpora, models, similarities

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# client = pymongo.MongoClient()
# db = client.github
# repos = db.repos

stoplist = set([line.strip('\n').strip() for line in open('stop-words.txt')])

# def iterator():
#     for repo in repos.find():
#         # join all content in each readme
#         words = ' '.join([p['content'] for p in repo['readme']]).split()
#         # filter words that are too short
#         words = [word for word in words if len(word) >= 3]
#         # one document at a time
#         yield words
#
# def compute_dictionary(savename):
#     dictionary = corpora.Dictionary(iterator())
#     stop_ids = [dictionary.token2id[stopword] for stopword in stoplist
#                 if stopword in dictionary.token2id]
#     # remove stop words and words that appear very few
#     dictionary.filter_tokens(stop_ids)
#     # remove gaps in id sequence after words that were removed
#     dictionary.compactify()
#     # remove extreme words
#     dictionary.filter_extremes(no_below=5, no_above=0.1, keep_n=100000)
#     # store the dictionary, for future reference
#     dictionary.save('%s.dict' % savename)
#     return dictionary
#
# def compute_vectors(dictionary, savename):
#     corpus = [dictionary.doc2bow(words) for words in iterator()]
#     # store to disk, for later use
#     corpora.MmCorpus.serialize('%.mm' % savename, corpus)
#     return corpus

def compute_tfidf(dictionary, corpus, load=False):
    if load:
        dictionary = corpora.Dictionary.load('%s.dict' % dictionary)
        corpus = corpora.MmCorpus('%s.mm' % corpus)
    # initialize a model
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    return corpus_tfidf

if __name__ == '__main__':
    SAVENAME = "readme"
    # dictionary = compute_dictionary(savename)
    # corpus = compute_vectors(dictionary, savename)
    corpus_tfidf = compute_tfidf(SAVENAME, SAVENAME, True)
    for doc in corpus_tfidf:
        print(doc)

