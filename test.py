import logging
import eval
import functools
import showcase_info as showcase
from user_based import compute as jaccard_model
import user_based_model
import text_based_model
import matplotlib.pyplot as plt

# def utest_find_mix1():
#     repo_name = 'knockout/knockout'
#     weighted_methods = [(jaccard_model.find_similar_repos_jaccard, 1)]
#     logging.info(str(weighted_methods))
#     repo_list = eval.find_mix(repo_name, weighted_methods)
#     print '[test] utest_find_mix1'
#     print repo_list

# def draw_comparison():
#     weighted_methods = [(jaccard_model.find_similar_repos_jaccard, 1)]
#     find_similar_repo_func = functools.partial(eval.find_mix, weighted_methods=weighted_methods)
#     eval_funs = [functools.partial(eval.eval_group_repos,
#                                    showcase.sc_frontend_javascript_frameworks,
#                                    find_similar_repo_func)]
#     eval.plot_comparison(eval_funs, ["m1"], ["long method name..."], "test")
#
def draw_precision_recall():
    weighted_methods = [(jaccard_time, 1)]
    find_similar_repo_func = functools.partial(eval.find_mix, weighted_methods=weighted_methods)
    pl, rl, f1 = eval.eval_single_repo("matplotlib/matplotlib", showcase.sc_data_visualization, find_similar_repo_func)
    eval.plot_precision_recall(pl, rl, "Depth-Score Curve Using User-based Jaccard with Time Range")

def draw_scores():
    weighted_methods = [(jaccard_time, 1)]
    find_similar_repo_func = functools.partial(eval.find_mix, weighted_methods=weighted_methods)
    pl, rl, f1 = eval.eval_single_repo("matplotlib/matplotlib", showcase.sc_data_visualization, find_similar_repo_func)
    eval.plot_f1score(f1, pl, rl, "Recall-Precision Curve Using User-based Jaccard with Time Range")
#
# def draw_group_scores(group_repos, weighted_methods, title):
#     find_similar_repo_func = functools.partial(eval.find_mix, weighted_methods=weighted_methods)
#     pl, rl, f1 = eval.eval_group_repos(group_repos, find_similar_repo_func)
#
#     eval.plot_f1score(f1, pl, rl, title)
#     eval.plot_precision_recall(pl, rl, title)

def draw_group_all(group_repos, methods, xticks=None, legends=None):
    eval_funs = []
    if legends is None:
        legends = []
    for wm in methods:
        title = ' + '.join([method_name.get(m, "User-based Jaccard with Time Range") for m, w in wm])
        legends.append(title)
        print "Processing: " + title
        find_similar_repo_func = functools.partial(eval.find_mix, weighted_methods=wm)
        eval_f = functools.partial(eval.eval_group_repos, group_repos, find_similar_repo_func)
        eval_funs.append(eval_f)
        pl, rl, f1 = eval_f()
        eval.plot_f1score(f1, pl, rl, "Depth-Score Curve Using " + title)
        eval.plot_precision_recall(pl, rl, "Recall-Precision Curve Using " + title)

    print "Processing Comparison..."
    length = len(methods)

    if xticks is None:
        xticks = ["Method " + str(i) for i in range(1, length+1)]

    # if legends is None:
    #     legends = ["Jaccard", "Time-aware Jaccard", "User-based LDA",
    #             "User-based TFIDF", "Text-based LDA", "Text-based TFIDF"]

    eval.plot_comparison(eval_funs, xticks, legends,
                         "Methods Comparison")


jaccard = jaccard_model.find_similar_repos_jaccard
jaccard_time = functools.partial(jaccard_model.find_similar_repos_jaccard_in_time_range, time_range_in_day=8)
user_based_lda = functools.partial(user_based_model.find_similar_repos, type="lda")
user_based_tfidf = functools.partial(user_based_model.find_similar_repos, type="tfidf")
text_based_lda = functools.partial(text_based_model.find_similar_repos, type="lda")
text_based_tfidf = functools.partial(text_based_model.find_similar_repos, type="tfidf")

method_name = {
    jaccard: "User-based Jaccard",
    jaccard_time: "User-based Jaccard with Time Range",
    user_based_lda: "User-based LDA",
    user_based_tfidf: "User-based TFIDF",
    text_based_lda: "Text-based LDA",
    text_based_tfidf: "Text-based TFIDF"
}

if __name__ == "__main__":
    single_methods = [
        [(jaccard, 1)],
        [(jaccard_time, 1)],
        [(user_based_lda, 1)],
        [(user_based_tfidf, 1)],
        [(text_based_lda, 1)],
        [(text_based_tfidf, 1)]
    ]

    mix_methods = [
        [(jaccard, 0.5), (jaccard_time, 0.5)],
        [(text_based_lda, 0.5), (text_based_tfidf, 0.5)],
        [(user_based_lda, 0.5), (user_based_tfidf, 0.5)],
        [(jaccard_time, 0.5), (user_based_lda, 0.5)],
        [(jaccard_time, 0.5), (user_based_tfidf, 0.5)],
        [(jaccard_time, 0.5), (text_based_lda, 0.5)],
        [(jaccard_time, 0.5), (text_based_tfidf, 0.5)],
    ]

    time_ranges = [1.0/256, 1.0/64, 1.0/16, 1.0/4, 1, 4, 16, 64, 256]
    time_varying_methods = [
        [(functools.partial(jaccard_model.find_similar_repos_jaccard_in_time_range, time_range_in_day=day), 1)]
        for day in time_ranges
    ]

    draw_group_all(showcase.sc_frontend_javascript_frameworks,
                   single_methods)
    plt.show()


    # draw_group_all(showcase.sc_frontend_javascript_frameworks,
    #                time_varying_methods,
    #                xticks=map(str, time_ranges),
    #                legends=["Time range: " + str(x) + " days" for x in time_ranges])
    # plt.show()

    # draw_group_all(showcase.sc_data_visualization,
    #                mix_methods, legends=[])
    # plt.show()

    # draw_precision_recall()
    # draw_scores()
    # plt.show()







