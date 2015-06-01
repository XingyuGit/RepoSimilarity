import eval_test1


if __name__ == '__main__':
    while (True):
        repo_name = raw_input("Enter your repository name: ")
        method = "user_based_jaccard_withtime"
        if eval_test1.user_based_jaccard.stars.has_key(repo_name):
            rank = eval_test1.find_similar_repo(repo_name, method)
            print sorted(rank.items(), key=lambda x: x[1])
        else:
            print "Name error!"