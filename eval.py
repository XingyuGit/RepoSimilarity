import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcol
import matplotlib.cm as cm

import showcase_info as showcase
from user_based import compute as user_based_jaccard
from user_based import user_based_model


def find_similar_repo(repo_name, method_name, rank=True):
    res = {}
    if method_name == "user_based_jaccard":
        res = user_based_jaccard.find_similar_repos(repo_name)
    elif method_name == "user_based_jaccard_withtime":
        res = user_based_jaccard.find_similar_repos_considering_time(repo_name, 7)
    elif method_name == "user_based_lda":
        res = user_based_model.find_similar_repos(repo_name, "lda")
    elif method_name == "user_based_tfidf":
        res = user_based_model.find_similar_repos(repo_name, "tfidf")
    elif method_name == "text_based_lda":
        pass
    elif method_name == "text_based_tfidf":
        pass

    if rank:
        res = [repo_name for repo_name, similarity in
            sorted(res.items(), key=lambda item: -item[1])]
        ranks = range(1, len(res)+1)
        res = dict(zip(res, ranks))
    return res


def merge_results(user_based_lda={}, user_based_tfidf={},
                  user_based_jaccard={}, user_based_jaccard_withtime={},
                  text_based_lda={}, text_based_tfidf={}):

    user_based_lda_weight = 0
    user_based_tfidf_weight = 0
    user_based_jaccard_weight = 1
    user_based_jaccard_withtime_weight = 0
    text_based_lda_weight = 0
    text_based_tfidf_weight = 0

    merged = {}

    for repo in user_based_lda:
        merged[repo] = merged.get(repo, 0) + user_based_lda_weight * user_based_lda[repo]

    for repo in user_based_tfidf:
        merged[repo] = merged.get(repo, 0) + user_based_tfidf_weight * user_based_tfidf[repo]

    for repo in user_based_jaccard:
        merged[repo] = merged.get(repo, 0) + user_based_jaccard_weight * user_based_jaccard[repo]

    for repo in user_based_jaccard_withtime:
        merged[repo] = merged.get(repo, 0) + user_based_jaccard_withtime_weight * user_based_jaccard_withtime[repo]

    for repo in text_based_lda:
        merged[repo] = merged.get(repo, 0) + text_based_lda_weight * text_based_lda[repo]

    for repo in text_based_tfidf:
        merged[repo] = merged.get(repo, 0) + text_based_tfidf_weight * text_based_tfidf[repo]

    return merged


def dict2list(dictionary):
    return [repo_name for repo_name, rank_score in
            sorted(dictionary.items(), key=lambda item: item[1])]


# return (precision, recall, F1score)
def eval(k, our_repos, showcase_repos):
    # cast to set
    showcase_repos = set(showcase_repos)
    our_repos = set(our_repos[:k])

    # number of common repos
    num_commons = len(our_repos.intersection(showcase_repos))
    num_commons = float(num_commons)

    # precision: num of repos in common / num of our repos
    precision = num_commons / k

    # recall: num of repos in common / num of showcase's repos
    recall = num_commons / len(showcase_repos)

    # F1score
    F1 = 2 * precision * recall / (precision + recall)

    return precision, recall, F1


def plot_precision_recall(precision_list, recall_list):

    cmap = cm.cool
    norm = matplotlib.colors.Normalize(vmin=1, vmax=100)

    # create a ScalarMappable and initialize a data structure
    scmap = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
    scmap.set_array([])

    depths = range(1, len(precision_list)+1)

    plt.plot(recall_list, precision_list, 'b*-')
    # plt.scatter(recall_list, precision_list, c=depths, cmap=cmap, norm=norm)
    # plt.colorbar(scmap, ticks=[1, 50, 100], label="Depth")


def plot_f1score(f1score_list):
    depths = range(1, len(f1score_list)+1)
    plt.plot(depths, f1score_list, 'b*-')


if __name__ == '__main__':
    # n = 100
    # X = np.random.normal(0,1,n)
    # Y = np.random.normal(0,1,n)

    rank = find_similar_repo("jashkenas/backbone", "user_based_jaccard")
    print str(rank) + "\n"
    rank = merge_results(user_based_jaccard=rank)
    print str(rank) + "\n"
    rank = dict2list(rank)
    print str(rank) + "\n"

    showcase_js = showcase.sc_frontend_javascript_frameworks

    precision_list = []
    recall_list = []
    f1score_list = []
    for i in range(1, len(rank)+1):
        precision, recall, f1score = eval(i, rank, showcase_js)
        precision_list.append(precision)
        recall_list.append(recall)
        f1score_list.append(f1score)

    fig = plt.figure(1)
    plot_f1score(f1score_list=f1score_list)
    fig = plt.figure(2)
    plot_precision_recall(recall_list=recall_list, precision_list=precision_list)
    plt.show()
