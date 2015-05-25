import pymongo
import re
from lxml import html
from lxml.html.clean import Cleaner
from pprint import pprint
import eventlet
from eventlet.green import urllib2
from base64 import b64encode
import json
import logging
import sys
import time

class Repo(object):

    stopwords = set([
        'examples', 'installation', 'contribute', 'building', 'build', 'prerequisites',
        'license', 'more', 'running', 'tests', 'install', 'source', 'development',
        'contributing', 'requirements', 'usage', 'other', 'copyright', 'running',
        'documentation', 'community', 'issue', 'homepage'
    ])

    whitelist = set([
        'description', 'introduction', 'overview'
    ])

    ignorewords = set([
        'a', 'an', 'the', 'of', 'for', 'the', 'to', 'in'
    ])

    nonalpha_re = re.compile(r"[^a-zA-Z'-]")
    url_re = re.compile(r"http(s?):\/\/\S*")

    # ---- stopwords ----

    def has_stopwords(self, text):
        if self.stopwords.intersection(set(text.split())):
            return True
        else:
            return False

    def add_stopwords(self, text):
        if text:
            new_stopwords = set(text.split()).difference(self.ignorewords)
            self.stopwords.update(new_stopwords)

    # ---- filter ----

    def filter_nonalpha(self, text):
        return self.nonalpha_re.sub(' ', text).strip()

    def filter_url(self, text):
        return self.url_re.sub(' ', text).strip()

    def filter_all(self, text):
        text = self.filter_url(text)
        return self.filter_nonalpha(text)

    # -----------------

    def dict(self):
        return { k: self.__dict__[k] for k in self.__dict__ if not k.startswith('_') }

    # ----- error ---------

    def not_found(self):
        return self._not_found

    def fatal_error(self):
        return self._fatal_error

    def error_msg(self):
        return self._error_msg

    def __init__(self, full_name, description, html_url):
        self.full_name = full_name
        self.html_url = html_url
        self.origin_description = description
        self.origin_readme = ""
        self.description = self.filter_all(description.lower())
        self.readme = []
        self._not_found = False
        self._fatal_error = False
        self._error_msg = ""

        retry = 3
        while True:
            try:
                self.retreive_data()
                break
            except urllib2.URLError, e:
                if hasattr(e, 'code') and 400 <= e.code < 500:
                    self._not_found = True
                    return
                else:
                    error_msg = "reason :" + e.reason
                    logging.error(error_msg)
                    logging.error("Retrying after 5 seconds...")
                    time.sleep(5)
                    retry -= 1
                    if retry < 0:
                        self._not_found = True
                        self._error_msg = error_msg
                        return
                    else:
                        continue
            except Exception, e:
                self._fatal_error = True
                self._error_msg = e.message
                return

    def retreive_data(self):
        page = urllib2.urlopen(self.html_url).read()
        tree = html.fromstring(page)
        readme_tree = tree.xpath('//*[@id="readme"]/article')

        if len(readme_tree) < 1:
            return

        readme_tree = readme_tree[0]
        self.origin_readme = readme_tree.text_content()
        cleaner = Cleaner(allow_tags=['p','h1','h2','h3','h4','h5','pre'], remove_unknown_tags=False)
        readme_tree = cleaner.clean_html(readme_tree)

        header = ""
        content = ""
        garbage_time = False

        # iterate each header and paragraph
        i = 0
        for sub in readme_tree.iterchildren():
            if sub is None:
                break

            if sub.tag == 'pre':
                self.add_stopwords(self.filter_all(header))
                header = ""
                continue

            if garbage_time:
                continue

            # header
            if sub.tag in ['h1','h2','h3','h4'] and sub.text is not None:
                # store last header and content
                if header and content:
                    header = self.filter_all(header)
                    content = self.filter_all(content)
                    self.readme.append({
                        'header': header,
                        'content': content
                    })
                    i += 1

                # get header
                header = sub.text.strip().lower()
                content = ""

                # keep the first paragraph, in whitelist; discard the one has stopwords
                if i >= 1 and header not in self.whitelist and \
                        self.has_stopwords(header):
                    garbage_time = True
                    header = ""

            # paragraph
            elif sub.tag in ['p'] and sub.text is not None:
                content += " " + sub.text.strip().lower()

        # store the last header and content
        if header and content:
            header = self.filter_all(header)
            content = self.filter_all(content)
            self.readme.append({
                'header': header,
                'content': content
            })

link_re = re.compile(r'rel="(.*)"')
link_url_re = re.compile(r'<(.*)>')
def link_parse(header):
    links = header.split(",")
    res = {}
    for str in links:
        rel = link_re.search(str).group(1)
        if rel is not None:
            res[rel] = { 'url': link_url_re.search(str).group(1) }
    return res


if __name__ == "__main__":
    api_url = 'https://api.github.com/repositories'
    client = pymongo.MongoClient()
    db = client['source']
    repos = db['repos']
    repos.create_index([("full_name", pymongo.ASCENDING)])

    pool = eventlet.GreenPool()

    n = 0
    while True:
        request = urllib2.Request(api_url)
        request.add_header('Authorization', 'Basic ' + b64encode('XingyuGit' + ':' + 'git631002'))
        response = urllib2.urlopen(request)
        # response = urllib2.urlopen(api_url).read()
        # print response.headers["X-RateLimit-Remaining"]

        link_header = link_parse(response.headers['link'])
        api_url = link_header.get('next').get('url') if link_header.get('next') is not None else ""

        if not api_url:
            break

        repos_json = json.loads(response.read())
        length = len(repos_json)

        def process_repo(repo_j):
            return Repo(repo_j['full_name'], repo_j['description'], repo_j['html_url'])

        for repo in pool.imap(process_repo, repos_json):
            if repo.not_found():
                logging.info('(NOT FOUND) url: %s , current_step: %d' % (repo.html_url, n))
            elif repo.fatal_error():
                logging.error('(FATAL ERROR) url: %s, current_step: %d' % (repo.html_url, n))
                logging.error('(FATAL ERROR) error_msg: %s' % repo.error_msg())
                sys.exit(0)
            else:
                if repos.find_one({ "full_name": repo.full_name }) is None:
                    repos.insert_one(repo.dict())


        n += length

        print "# processed: %d" % n
        print "%d stopwords: %s\n" % (len(Repo.stopwords), Repo.stopwords)

    print "TOTAL NUMBER: %d" % n



