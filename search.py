from user_based import compute as jaccard_model
from global_import import stars
import pprint

if __name__ == '__main__':
    while (True):
        repo_name = raw_input("Enter your repository name: ")
        if stars.has_key(repo_name):
            res = jaccard_model.find_similar_repos_jaccard_in_time_range(repo_name, 2)
            print pprint.pprint(res)
        else:
            print "Name error!"