import os
import redis
import heapq

MIN_STARS = 150
NUM_TOP_REPOS = 100
MAX_USER_NUM = 500
r = redis.StrictRedis(host='localhost', port=6379, db=0)

#@profile
def find_similar_repos_from(repo_name):
  repo_dict = dict()
  repo_jaccard_dict = dict()
  count_from_repo = r.scard('repo:'+repo_name)
  users = r.smembers('repo:'+repo_name)
  for user in users:
    #print '==user:'+user
    user_repos = r.smembers('login:'+user)
    count_user_stars = r.scard('login:'+user)
    if count_user_stars > MAX_USER_NUM:
      continue
    for user_repo in user_repos:
      #print '====repo:'+user_repo
      if not repo_dict.has_key(user_repo):
        repo_dict[user_repo] = 1
      else:
        repo_dict[user_repo] += 1
  for to_repo in repo_dict:
    count_common = repo_dict[to_repo]
    count_to_repo = r.scard('repo:'+to_repo)
    jaccard = 1.0*count_common/(count_to_repo+count_from_repo-count_common)
    # print '====repo:'+to_repo
    # print '====:'+str(count_common)+':'+str(count_to_repo)
    # print '====:'+str(jaccard)
    repo_jaccard_dict[to_repo]=jaccard
  k_keys_sorted_by_values = heapq.nlargest(NUM_TOP_REPOS, repo_jaccard_dict, key=repo_jaccard_dict.get)
  result_dict = dict()
  for to_repo in k_keys_sorted_by_values:
    result_dict[to_repo]=repo_jaccard_dict[to_repo]
  return result_dict

if __name__ == '__main__':
  my_dict = find_similar_repos_from('knockout/knockout')
  my_list = sorted(my_dict.items(), key=lambda x: x[1])
  print my_list
