import os
import redis
import logging
import time
import heapq
import pickle
import scipy.stats

NUM_TOP_REPOS = 100
LOG_ROW_FREQ = 100000
LOG_FILE_NAME = 'compute.log'
NUM_SEC_A_DAY = 86400    # 86400 ms in a day

r = redis.StrictRedis(host='localhost', port=6379, db=0)
# logging.basicConfig(filename=LOG_FILE_NAME,level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')

print 'start loading pickle stars'
stars = pickle.load(open('stars.pk', 'r'))
print 'load pickle stars complete'


# key: user, value: list
cached_user_repo_time = {}

# cache_find_similar_repos_jaccard[num_best][repo_name] = [('repo1', 1), ('repo2', 0.5), ...]
cache_find_similar_repos_jaccard = {}

# cache_find_similar_repos_jaccard_in_time_range[num_best][repo_name][time_range_in_day] = [('repo1', 1), ('repo2', 0.5), ...]
cache_find_similar_repos_jaccard_in_time_range = {}

# cache_find_similar_repos_jaccard_with_time_weight[num_best][repo_name][std] = [('repo1', 1), ('repo2', 0.5), ...]
cache_find_similar_repos_jaccard_with_time_weight = {}

# @profile
def find_similar_repos_jaccard(from_repo_name, num_best = 100):
    # check cache
    if cache_find_similar_repos_jaccard.has_key((from_repo_name, num_best)):
        return cache_find_similar_repos_jaccard[(from_repo_name, num_best)]

    repo_dict = {}
    # num_star_of_from_repo = r.scard('repo:' + from_repo_name)
    num_star_of_from_repo = stars.get(from_repo_name, 0)
    users = r.smembers('repo:' + from_repo_name)
    for user in users:
        # get all repos the user starred
        user_starred_repos = r.zrange('user:' + user, 0, -1)

        for user_starred_repo in user_starred_repos:
            if not repo_dict.has_key(user_starred_repo):
                repo_dict[user_starred_repo] = {}
                repo_dict[user_starred_repo]['count_common_stars'] = 1
            else:
                repo_dict[user_starred_repo]['count_common_stars'] += 1

    repo_jaccard_dict = {}
    for to_repo in repo_dict:
        count_common_stars = repo_dict[to_repo]['count_common_stars']
        # num_star_of_to_repo = r.scard('repo:' + to_repo)
        num_star_of_to_repo = stars.get(to_repo, 0)
        jaccard_similarity = 1.0 * count_common_stars / (num_star_of_to_repo + num_star_of_from_repo - count_common_stars)
        repo_dict[to_repo]['jaccard_similarity'] = jaccard_similarity
        repo_jaccard_dict[to_repo] = jaccard_similarity

    top_ranked_repos = heapq.nlargest(num_best, repo_jaccard_dict, key=repo_jaccard_dict.get)
    
    result_list = []
    for to_repo in top_ranked_repos:
        result_list.append((to_repo, repo_dict[to_repo]['jaccard_similarity']))

    # store result_list to cache
    cache_find_similar_repos_jaccard[(from_repo_name, num_best)] = result_list

    return result_list

def find_similar_repos_jaccard_in_time_range(from_repo_name, time_range_in_day, num_best=100):
    # check cache
    if cache_find_similar_repos_jaccard_in_time_range.has_key((from_repo_name, time_range_in_day, num_best)):
        return cache_find_similar_repos_jaccard_in_time_range[(from_repo_name, time_range_in_day, num_best)]

    repo_dict = {}
    # num_star_of_from_repo = r.scard('repo:' + from_repo_name)
    num_star_of_from_repo = stars.get(from_repo_name, 0)
    users = r.smembers('repo:' + from_repo_name)
    for user in users:
        # get the time the user performed the starring event, type: float, millisec since epoch
        user_star_from_repo_time = r.zscore('user:' + user, from_repo_name)

        # get the repos the user starred in a given time range
        half_time_range = NUM_SEC_A_DAY * time_range_in_day / 2.0
        min_time = user_star_from_repo_time - half_time_range
        max_time = user_star_from_repo_time + half_time_range

        # get partial repos the user starred, within time range
        user_starred_repos = r.zrangebyscore('user:' + user, min_time, max_time)

        for user_starred_repo in user_starred_repos:
            if not repo_dict.has_key(user_starred_repo):
                repo_dict[user_starred_repo] = {}
                repo_dict[user_starred_repo]['count_common_stars'] = 1
            else:
                repo_dict[user_starred_repo]['count_common_stars'] += 1

    repo_jaccard_dict = {}
    for to_repo in repo_dict:
        count_common_stars = repo_dict[to_repo]['count_common_stars']
        # num_star_of_to_repo = r.scard('repo:' + to_repo)
        num_star_of_to_repo = stars.get(to_repo, 0)
        jaccard_similarity = 1.0 * count_common_stars / (num_star_of_to_repo + num_star_of_from_repo - count_common_stars)
        repo_dict[to_repo]['jaccard_similarity'] = jaccard_similarity
        repo_jaccard_dict[to_repo] = jaccard_similarity

    top_ranked_repos = heapq.nlargest(num_best, repo_jaccard_dict, key=repo_jaccard_dict.get)
    
    result_list = []
    for to_repo in top_ranked_repos:
        result_list.append((to_repo, repo_dict[to_repo]['jaccard_similarity']))

    # store result_list to cache
    cache_find_similar_repos_jaccard_in_time_range[(from_repo_name, time_range_in_day, num_best)] = result_list

    return result_list

# std is the standard deviation for the normal distribution
# if std is 1, we we focus on starring events within +-1 day
# if std is 2, we we focus on starring events within +-2 day
# suggusted std value could be 0.25, 0.5, 1, 2, 4, 8, 16...
def find_similar_repos_jaccard_with_time_weight(from_repo_name, std, num_best = 100):
    # check cache
    if cache_find_similar_repos_jaccard_with_time_weight.has_key((from_repo_name, std, num_best)):
        return cache_find_similar_repos_jaccard_with_time_weight[(from_repo_name, std, num_best)]

    repo_dict = {}
    # num_star_of_from_repo = r.scard('repo:' + from_repo_name)
    num_star_of_from_repo = stars.get(from_repo_name, 0)
    users = r.smembers('repo:' + from_repo_name)
    my_norm = scipy.stats.norm(0, std)
    for user in users:
        # get the time the user performed the starring event, type: float, millisec since epoch
        user_star_from_repo_time = r.zscore('user:' + user, from_repo_name)

        # get all repos the user starred, with the times
        if not cached_user_repo_time.has_key(user):
            user_starred_repos_and_times = r.zrange('user:' + user, 0, -1, withscores=True)
            cached_user_repo_time[user] = user_starred_repos_and_times
        else:
            user_starred_repos_and_times = cached_user_repo_time[user]

        for user_starred_repo_and_time in user_starred_repos_and_times:
            user_starred_repo = user_starred_repo_and_time[0]
            user_starred_time = user_starred_repo_and_time[1]

            # transform time to count_weight
            diff_day_num = (user_starred_time - user_star_from_repo_time) / NUM_SEC_A_DAY
            count_weight = my_norm.pdf(diff_day_num)

            if not repo_dict.has_key(user_starred_repo):
                repo_dict[user_starred_repo] = {}
                repo_dict[user_starred_repo]['count_common_stars'] = count_weight
            else:
                repo_dict[user_starred_repo]['count_common_stars'] += count_weight

    repo_jaccard_dict = {}
    for to_repo in repo_dict:
        count_common_stars = repo_dict[to_repo]['count_common_stars']
        # num_star_of_to_repo = r.scard('repo:' + to_repo)
        num_star_of_to_repo = stars.get(to_repo, 0)
        jaccard_similarity = 1.0 * count_common_stars / (num_star_of_to_repo + num_star_of_from_repo - count_common_stars)
        repo_dict[to_repo]['jaccard_similarity'] = jaccard_similarity
        repo_jaccard_dict[to_repo] = jaccard_similarity

    top_ranked_repos = heapq.nlargest(NUM_TOP_REPOS, repo_jaccard_dict, key=repo_jaccard_dict.get)
    
    result_list = []
    for to_repo in top_ranked_repos:
        result_list.append((to_repo, repo_dict[to_repo]['jaccard_similarity']))

    # store result_list to cache
    cache_find_similar_repos_jaccard_with_time_weight[(from_repo_name, std, num_best)] = result_list

    return result_list

if __name__ == '__main__':
    test_repo_name = 'jashkenas/backbone'

    # my_list = find_similar_repos_jaccard(test_repo_name)
    # my_list = find_similar_repos_jaccard_in_time_range(test_repo_name, 2)
    my_list = find_similar_repos_jaccard_with_time_weight(test_repo_name, 1)

    print my_list
