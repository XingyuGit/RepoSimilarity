import logging
import evaluation
from user_based import compute as jaccard_model

def utest_find_mix1():
    repo_name = 'knockout/knockout'
    weighted_methods = [(jaccard_model.find_similar_repos_jaccard, 1)]
    logging.info(str(weighted_methods))
    repo_list = evaluation.find_mix(repo_name, weighted_methods)
    print '[test] utest_find_mix1'
    print repo_list



if __name__ == "__main__":
    logging.basicConfig(filename='test.log',level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')
    utest_find_mix1()