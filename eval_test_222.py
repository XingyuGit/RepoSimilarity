import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import showcase_info as showcase
import logging
import functools

# import compute
# matplotlib.use('GTKAgg')


LOG_FILE_NAME = 'eval_test.log'
logging.basicConfig(filename=LOG_FILE_NAME,level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')

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

def plot_precision_recall(precision_list, recall_list, title):
    fig = plt.figure()
    plt.plot(recall_list, precision_list, 'b.-')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(title)
    plt.legend()

def plot_f1score(f1score_list, precision_list, recall_list, title):
    depths = range(1, len(f1score_list)+1)
    fig = plt.figure()
    plt.plot(depths, precision_list, 'b-')
    plt.plot(depths, recall_list, 'r-')
    plt.plot(depths, f1score_list, 'm-')
    plt.xlabel("Depths")
    plt.ylabel('Scores')
    plt.title(title)
    plt.legend()

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


# def eval_within_group(repo_group_names, find_similar_repos_func):

#     # NUM_TOP_REPOS = 100, [0,0,0,...]
#     sum_precision_list = [0] * compute.NUM_TOP_REPOS
#     sum_recall_list = [0] * compute.NUM_TOP_REPOS
#     sum_f1score_list = [0] * compute.NUM_TOP_REPOS

#     for current_repo_name in repo_group_names:

#         res_dict = find_similar_repos_func(current_repo_name)
#         rank_list = [repo_name for repo_name, sim in
#             sorted(res_dict.items(), key=lambda x: -x[1])]

#         for depth in range(0, len(rank_list)):
#             precision, recall, f1score = eval(depth+1, rank_list, repo_group_names)
#             sum_precision_list[depth]+=precision
#             sum_recall_list[depth]+=recall
#             sum_f1score_list[depth]+=f1score

#     group_size = len(repo_group_names)
#     mean_precision_list = [x / group_size for x in sum_precision_list]
#     mean_recall_list = [x / group_size for x in sum_recall_list]
#     mean_f1score_list = [x / group_size for x in sum_f1score_list]

#     return mean_precision_list, mean_recall_list, mean_f1score_list

# def eval_time_with_std(test_repo_name):
#     # for std in [0.5, 1, 2, 4, 8]:
#     for std in [1, 2]:
#         precision_list = []
#         recall_list = []
#         f1score_list = []

#         res_dict = compute.find_similar_repos_considering_time_range_all(test_repo_name, std)
#         rank_list = [repo_name for repo_name, sim in
#             sorted(res_dict.items(), key=lambda x: -x[1])]

#         for depth in range(1, len(rank_list)+1):
#             precision, recall, f1score = eval(depth, rank_list, showcase_js)
#             precision_list.append(precision)
#             recall_list.append(recall)
#             f1score_list.append(f1score)

#         plot_f1score(f1score_list=f1score_list, precision_list=precision_list, 
#             recall_list=recall_list, title = 'std='+str(std))

#         plot_precision_recall(recall_list=recall_list, precision_list=precision_list, 
#             title = 'std='+str(std))

# def eval_time_with_range(test_repo_name):
#     # for time_range in [0.5, 1, 2, 4, 8]:
#     for time_range in [1, 2]:
#         precision_list = []
#         recall_list = []
#         f1score_list = []

#         res_dict = compute.find_similar_repos_considering_time(test_repo_name, time_range)
#         rank_list = [repo_name for repo_name, sim in
#             sorted(res_dict.items(), key=lambda x: -x[1])]

#         for depth in range(1, len(rank_list)+1):
#             precision, recall, f1score = eval(depth, rank_list, showcase_js)
#             precision_list.append(precision)
#             recall_list.append(recall)
#             f1score_list.append(f1score)

#         plot_f1score(f1score_list=f1score_list, precision_list=precision_list, 
#             recall_list=recall_list, title='time_range='+str(time_range))

#         plot_precision_recall(recall_list=recall_list, precision_list=precision_list, 
#             title='time_range='+str(time_range))

# if __name__ == '__main__':
#     test_repo_name = 'jashkenas/backbone'
#     showcase_js = showcase.sc_frontend_javascript_frameworks

#     # eval_time_with_std(test_repo_name)
#     # eval_time_with_range(test_repo_name)
#     precision_list, recall_list, f1score_list = 
#         eval_within_group(showcase_js, functools.partial(compute.find_similar_repos_considering_time, time_range_in_day=8))

#     plot_f1score(f1score_list=f1score_list, precision_list=precision_list, 
#             recall_list=recall_list, title = 'repo group:'+str(repo_group_names))

#     plot_precision_recall(recall_list=recall_list, precision_list=precision_list, 
#             title = 'repo group:'+str(repo_group_names))
#     plt.show()

