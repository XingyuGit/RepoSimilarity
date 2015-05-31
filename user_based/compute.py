import os
import redis
import logging
import time
import heapq
import pickle

MIN_STARS = 150
NUM_TOP_REPOS = 100
LOG_ROW_FREQ = 100000
LOG_FILE_NAME = 'compute.log'
NUM_SEC_A_DAY = 86400    # 86400 ms in a day

r = redis.StrictRedis(host='localhost', port=6379, db=0)
logging.basicConfig(filename=LOG_FILE_NAME,level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')

stars = pickle.load(open('stars.pk', 'r'))

#@profile
def find_similar_repos(from_repo_name):
    repo_dict = dict()
    # num_star_of_from_repo = r.scard('repo:' + from_repo_name)
    num_star_of_from_repo = stars.get(from_repo_name, 0)
    users = r.smembers('repo:' + from_repo_name)
    for user in users:
        # get all repos the user starred
        user_starred_repos = r.zrange('user:' + user, 0, -1)

        for user_starred_repo in user_starred_repos:
            if not repo_dict.has_key(user_starred_repo):
                repo_dict[user_starred_repo] = dict()
                repo_dict[user_starred_repo]['count_common_stars'] = 1
            else:
                repo_dict[user_starred_repo]['count_common_stars'] += 1

    repo_jaccard_dict = dict()
    for to_repo in repo_dict:
        count_common_stars = repo_dict[to_repo]['count_common_stars']
        num_star_of_to_repo = stars.get(to_repo, 0)
        jaccard_similarity = 1.0 * count_common_stars / (num_star_of_to_repo + num_star_of_from_repo - count_common_stars)
        repo_dict[to_repo]['jaccard_similarity'] = jaccard_similarity
        repo_jaccard_dict[to_repo] = jaccard_similarity

    k_keys_sorted_by_values = heapq.nlargest(NUM_TOP_REPOS, repo_jaccard_dict, key=repo_jaccard_dict.get)
    
    result_dict = dict()
    for to_repo in k_keys_sorted_by_values:
        result_dict[to_repo] = repo_dict[to_repo]['jaccard_similarity']
    return result_dict

def find_similar_repos_considering_time(from_repo_name, time_range_in_day):
    repo_dict = dict()
    num_star_of_from_repo = stars.get(from_repo_name, 0)
    users = r.smembers('repo:' + from_repo_name)
    for user in users:
        # get the time the user performed the starring event, type: float, millisec since epoch
        user_star_from_repo_time = r.zscore('user:' + user, from_repo_name)

        # get the repos the user starred in a given time range
        half_time_range = NUM_SEC_A_DAY * time_range_in_day / 2.0
        min_time = user_star_from_repo_time - half_time_range
        max_time = user_star_from_repo_time + half_time_range

        # degub
        user_starred_repos_0 = r.zrange('user:' + user, 0, -1)
        logging.info('==all==')
        logging.info(user_starred_repos_0)

        
        user_starred_repos = r.zrangebyscore('user:' + user, min_time, max_time)
        logging.info('==time==')

        logging.info('middle: '+str(user_star_from_repo_time))
        logging.info('middle: '+time.ctime(user_star_from_repo_time))

        logging.info('min: '+str(min_time)+' max: '+str(max_time))
        logging.info('min: '+time.ctime(min_time)+ ' max: '+time.ctime(max_time))
        
        logging.info(user_starred_repos)

        for user_starred_repo in user_starred_repos:
            if not repo_dict.has_key(user_starred_repo):
                repo_dict[user_starred_repo] = dict()
                repo_dict[user_starred_repo]['count_common_stars'] = 1
            else:
                repo_dict[user_starred_repo]['count_common_stars'] += 1

    repo_jaccard_dict = dict()
    for to_repo in repo_dict:
        count_common_stars = repo_dict[to_repo]['count_common_stars']
        num_star_of_to_repo = stars.get(to_repo, 0)
        jaccard_similarity = 1.0 * count_common_stars / (num_star_of_to_repo + num_star_of_from_repo - count_common_stars)
        repo_dict[to_repo]['jaccard_similarity'] = jaccard_similarity
        repo_jaccard_dict[to_repo] = jaccard_similarity

    top_ranked_repos = heapq.nlargest(NUM_TOP_REPOS, repo_jaccard_dict, key=repo_jaccard_dict.get)
    
    result_dict = dict()
    for to_repo in top_ranked_repos:
        result_dict[to_repo] = repo_dict[to_repo]['jaccard_similarity']
    return result_dict

if __name__ == '__main__':
    from_repo_name = 'jashkenas/backbone'
    # my_dict = find_similar_repos(from_repo_name)
    my_dict = find_similar_repos_considering_time(from_repo_name, 4)
    my_list = sorted(my_dict.items(), key=lambda x: -x[1])
    print my_list
