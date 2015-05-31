import eval


if __name__ == '__main__':
    while (True):
        repo_name = raw_input("Enter your repository name: ")
        method = "user_based_jaccard_withtime"
        if eval.user_based_jaccard.stars.has_key(repo_name):
            rank = eval.find_similar_repo(repo_name, method)
            print sorted(rank.items(), key=lambda x: x[1])
        else:
            print "Name error!"