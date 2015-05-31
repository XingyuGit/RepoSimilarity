from user_based import compute as user_based_jaccard
from user_based import user_based_model
import eval

if __name__ == '__main__':
    while (True):
        repo_name = input("Enter your repository name: ")
        method = "user_based_jaccard_withtime"
        rank = eval.find_similar_repo(repo_name, method)
        print rank