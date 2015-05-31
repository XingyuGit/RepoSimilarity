import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcol
import matplotlib.cm as cm

def merge_results(user_based_lda={}, user_based_tfidf={},
                  user_based_jaccard={}, user_based_jaccard_withtime={},
                  text_based_lda={}, text_based_tfidf={}):

    user_based_lda_weight = 1
    user_based_tfidf_weight = 1
    user_based_jaccard_weight = 1
    user_based_jaccard_withtime_weight = 1
    text_based_lda_weight = 1
    text_based_tfidf_weight = 1

    merged = {}

    for repo in user_based_lda:
        merged.set(repo, merged.get(repo, 0) + user_based_lda_weight * user_based_lda[repo])

    for repo in user_based_tfidf:
        merged.set(repo, merged.get(repo, 0) + user_based_tfidf_weight * user_based_tfidf[repo])

    for repo in user_based_jaccard:
        merged.set(repo, merged.get(repo, 0) + user_based_jaccard_weight * user_based_jaccard[repo])

    for repo in user_based_jaccard_withtime:
        merged.set(repo, merged.get(repo, 0) + user_based_jaccard_withtime_weight * user_based_jaccard_withtime[repo])

    for repo in text_based_lda:
        merged.set(repo, merged.get(repo, 0) + text_based_lda_weight * text_based_lda[repo])

    for repo in text_based_tfidf:
        merged.set(repo, merged.get(repo, 0) + text_based_tfidf_weight * text_based_tfidf[repo])

    return merged

def dict2list(dictionary):
    return [repo_name for repo_name, rank_score in
            sorted(enumerate(dictionary), key=lambda item: item[1])]

# return (precision, recall, F1score)
def eval(k, our_repos, showcase_repos):
    # cast to set
    showcase_repos = set(showcase_repos)
    our_repos = set(our_repos[:k])

    # number of common repos
    num_commons = len(our_repos.intersection(showcase_repos))

    # precision: num of repos in common / num of our repos
    precision = num_commons / k

    # recall: num of repos in common / num of showcase's repos
    recall = num_commons / len(showcase_repos)

    # F1score
    F1 = 2 * precision * recall / (precision + recall)

def plot_precision_recall(precision_list, recall_list):
    # Make a user-defined colormap.
    cmap = mcol.LinearSegmentedColormap.from_list("MyCmapName",["r","b"])

    # Make a normalizer
    norm = mcol.Normalize(vmin=1, vmax=100)

    # Turn these into an object that can be used to map depth values to colors and
    # can be passed to plt.colorbar().
    # cpick = cm.ScalarMappable(norm=cnorm, cmap=cm1)
    # cpick.set_array([])

    depths = range(1, len(precision_list)+1)
    # colors = [cpick.to_rgba(depths) for d in depths]
    cmap = cm.jet

    plt.scatter(recall_list, precision_list, c=depths, cmap=cmap, norm=norm)
    # plt.colorbar(cpick, label="Depth")

def plot_f1score(f1score_list):
    depths = range(1, len(f1score_list)+1)
    plt.plot(depths, f1score_list)

if __name__ == '__main__':
    n = 100
    X = np.random.normal(0,1,n)
    Y = np.random.normal(0,1,n)

    print matplotlib.get_backend()

    plot_f1score(Y)

    # plot_precision_recall(X, Y)
