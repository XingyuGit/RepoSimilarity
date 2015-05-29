import pickle
import re

fullname_re = re.compile(r'http(s?)://github.com/(.*)')
def fullname_from_url(url):
    return fullname_re.search(url).group(2)

stars = {}

with open('repo_stars.csv') as f:
    all_lines = f.read().splitlines()
    all_lines = all_lines[1:] # get rid of header line

    for line in all_lines:
        url, num_stars = line.split(",")
        full_name = fullname_from_url(url)
        stars[full_name] = num_stars

    pickle.dump(stars, open('stars', 'w'))


stars = pickle.load(open('stars', 'r'))
print stars["andymccurdy/redis-py"]