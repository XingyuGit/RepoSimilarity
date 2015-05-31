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


# mix_ranks: {"m1": {"repo1": 1, "repo2": 2, ...}, ...}
# mix_weights: {"m1":0.3, "m2":0.7}
def merge_results(mix_ranks, mix_weights):
    merged = {}
    for method in mix_ranks:
        rank = mix_ranks[method] # {"repo1": 1, "repo2": 2, ...}
        weight = mix_weights[method] # 0.3
        for repo in rank:
            merged[repo] = merged.get(repo, 0) + weight * rank[repo]
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


def plot_f1score(f1score_list, precision_list, recall_list):
    depths = range(1, len(f1score_list)+1)
    plt.plot(depths, precision_list, 'b-')
    plt.plot(depths, recall_list, 'r-')
    plt.plot(depths, f1score_list, 'm-')


def plot_comparison(f1score_dict):
    method_list = []
    f1score_max_list = []
    for method in f1score_dict:
        f1score_list = f1score_dict[method]
        f1score_max = max(f1score_list)
        method_list.append(method)
        f1score_max_list.append(f1score_max)
    plt.bar(method_list, f1score_max_list, color="blue")
    plt.xlabel('Methods')
    plt.ylabel('Best F1Scores')
    plt.title('Comparison of different methods')
    plt.legend()

if __name__ == '__main__':

    query_repo_name = "jashkenas/backbone"
    showcase_js = showcase.sc_frontend_javascript_frameworks


    all_methods = ["user_based_jaccard", "user_based_jaccard_withtime",
                   "user_based_lda", "user_based_tfidf",
                   "text_based_lda", "text_based_tfidf"]

    mix1 = {"user_based_jaccard":1}
    mix2 = {"user_based_jaccard_withtime":1}
    mix3 = {"user_based_lda":1}
    mix4 = {"user_based_tfidf":1}
    mix5 = {"user_based_jaccard_withtime":0.5, "user_based_tfidf":0.5}
    mix6 = {"user_based_jaccard":0.5, "user_based_lda":0.5}
    query_methods = [mix1, mix2, mix3, mix4, mix5, mix6]

    similar_repos_all_methods = {}
    for method in all_methods:
        similar_repos_all_methods[method] = find_similar_repo(query_repo_name, method)

    f1score_dict = {}
    for mix_method in query_methods:
        mix_ranks = {}
        mix_weights = {}
        for m in mix_method:
            mix_ranks[m] = similar_repos_all_methods[m]
            mix_weights[m] = mix_method[m]
        rank = merge_results(mix_ranks, mix_weights)
        rank = dict2list(rank)

        precision_list = []
        recall_list = []
        f1score_list = []
        for i in range(1, len(rank)+1):
            precision, recall, f1score = eval(i, rank, showcase_js)
            precision_list.append(precision)
            recall_list.append(recall)
            f1score_list.append(f1score)
        f1score_dict[str(mix_method)] = f1score_list

        fig = plt.figure()
        plot_f1score(f1score_list=f1score_list, precision_list=precision_list, recall_list=recall_list)
        plt.xlabel("Depths")
        plt.ylabel('Scores')
        plt.title(str(mix_method))
        plt.legend()

        fig = plt.figure()
        plot_precision_recall(recall_list=recall_list, precision_list=precision_list)
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title(str(mix_method))
        plt.legend()

    fig = plt.figure()
    plot_comparison(f1score_dict)

    plt.show()
