import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.font_manager as fm


def find_mix(repo_name, weighted_method, use_rank=True, bsorted=True):
    repo_sims_dict = {}
    for f, w in weighted_method:
        sims = f(repo_name)
        if not bsorted:
            sims = sorted(sims, key=lambda x: -x[1])
        if use_rank:
            sims = [(r, i+1) for i, (r, s) in enumerate(sims)]
        for r, s in sims:
            repo_sims_dict[r] = repo_sims_dict.get(r, 0) + w * s

    # use_rank -> asc, otherwise -> desc
    repo_score_list = sorted(repo_sims_dict.items(), key=lambda x: x[1] if use_rank else -x[1])
    repo_ordered_list = [r for r, s in repo_score_list]
    return repo_ordered_list


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
    F1 = 2 * precision * recall / (precision + recall) if precision + recall != 0 else 0

    return precision, recall, F1


def plot_precision_recall(precision_list, recall_list, title=""):
    fig = plt.figure()
    plt.plot(recall_list, precision_list, 'b.-')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(title)
    plt.legend()
    plt.show()


def plot_f1score(f1score_list, precision_list, recall_list, title=""):
    depths = range(1, len(f1score_list)+1)
    fig = plt.figure()
    plt.plot(depths, precision_list, 'b-')
    plt.plot(depths, recall_list, 'r-')
    plt.plot(depths, f1score_list, 'm-')
    plt.xlabel("Depths")
    plt.ylabel('Scores')
    plt.title(title)
    plt.legend()
    plt.show()


def plot_comparison(eval_funs, methods_short=[], methods_long=[], title=""):

    length = len(eval_funs)

    max_f1score_list = []
    for f in eval_funs():
        plist, rlist, f1list = eval_funs()
        f1score_max = max(f1list)
        max_f1score_list.append(f1score_max)

    bar_width = 0.7
    index = np.arange(length)
    color = cm.rainbow(np.linspace(0,1,length))

    fig = plt.figure()
    barlist = plt.bar(index + bar_width, max_f1score_list, width=bar_width, color=color)

    plt.xticks(index + 1.5*bar_width, methods_short)
    plt.xlabel('Methods')
    plt.ylabel('Best F1Scores')
    plt.title(title)

    fontP = fm.FontProperties()
    fontP.set_size('small')
    lgd = plt.legend(barlist, [": ".join(t) for t in zip(methods_short, methods_long)],
                loc='upper center', bbox_to_anchor=(0.5, 1.25),
                ncol=2, fancybox=True, shadow=True, prop = fontP)

    fig.savefig('image_output.png', dpi=300, format='png', bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.show()


# test_repo_name = 'lalala/lalala'
# compared_repos = ['repo1', 'repo2', ...]
# my_function = [(f1, 0.5), (f2, 0.5)]
# return three lists: precision_list, recall_list, f1score_list
def eval_single_repo(test_repo_name, compared_repos, find_similar_repos_func):
    precision_list = []
    recall_list = []
    f1score_list = []

    # ranked_similar_repos: list of repo names in sorted order
    ranked_similar_repos = find_similar_repos_func(test_repo_name)

    for depth in range(1, len(ranked_similar_repos)+1):
        precision, recall, f1score = eval(depth, ranked_similar_repos, compared_repos)
        precision_list.append(precision)
        recall_list.append(recall)
        f1score_list.append(f1score)

    return precision_list, recall_list, f1score_list


def eval_group_repos(group_repos, find_similar_repos_func):
    sum_precision_list = []
    sum_recall_list = []
    sum_f1score_list = []

    empty_sum_lists = True
    for current_repo in group_repos:
        precision_list, recall_list, f1score_list = eval_single_repo(current_repo, group_repos, find_similar_repos_func)
        if empty_sum_lists:
            sum_precision_list = precision_list
            sum_recall_list = recall_list
            sum_f1score_list = f1score_list
            empty_sum_lists = False
        else:
            sum_precision_list = [a + b for a, b in zip(sum_precision_list, precision_list)]
            sum_recall_list = [a + b for a, b in zip(sum_recall_list, recall_list)]
            sum_f1score_list = [a + b for a, b in zip(sum_f1score_list, f1score_list)]

    group_size = len(group_repos)
    mean_precision_list = [x / group_size for x in sum_precision_list]
    mean_recall_list = [x / group_size for x in sum_recall_list]
    mean_f1score_list = [x / group_size for x in sum_f1score_list]

    return mean_precision_list, mean_recall_list, mean_f1score_list

import functools
import showcase_info as showcase
from user_based import compute as user_based_jaccard
import user_based_model
import text_based_model

if __name__ == "__main__":
    pass
