import pymongo
import re
from lxml import html
from lxml.html.clean import Cleaner
import eventlet
from eventlet.green import urllib2
from pprint import pprint
import logging
import sys
import time

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

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

    ignorewords = set([line.strip('\n').strip() for line in open('stopwords.txt')])

    nonalpha_re = re.compile(r"[^a-zA-Z'-]")
    url_re = re.compile(r"http(s?):\/\/\S*")

    # ---- stopwords ----

    def has_stopwords(self, text):
        if self.whitelist.intersection(set(text.split())):
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

    def __init__(self, full_name, html_url, description=""):
        self.full_name = full_name
        self.html_url = html_url
        self.origin_description = description
        self.origin_readme = ""
        self.description = ""
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
                    error_msg = "reason :" + str(e.reason)
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
        r = urllib2.urlopen(self.html_url)
        page = r.read()
        tree = html.fromstring(page)

        # get description part
        description_tree = tree.xpath('//*[@class="repository-description"]/text()')
        if len(description_tree) > 0:
            self.origin_description = description_tree[0].strip().lower()
            self.description = self.filter_all(self.origin_description)

        # get readme part
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


fullname_re = re.compile(r'http(s?)://github.com/(.*)')
def fullname_from_url(url):
    return fullname_re.search(url).group(2)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    else:
        n = 0

    valid_n = 0

    client = pymongo.MongoClient()
    db = client['source']
    repos = db['repos']
    repos.create_index([("full_name", pymongo.ASCENDING)])

    pool = eventlet.GreenPool()

    with open('all_repos.csv') as f:
        print "Start getting repo list..."

        all_urls = f.read().splitlines()
        all_urls = all_urls[1:] # get rid of header line

        step = 1000
        total_length = len(all_urls)

        print "Repo list ready."

        while n < total_length:
            rlimit = min(total_length, n + step)
            urls = all_urls[n:rlimit]

            def process_repo(url):
                return Repo(fullname_from_url(url), url)

            for repo in pool.imap(process_repo, urls):
                if repo.not_found():
                    logging.info('(NOT FOUND) url: %s , current_step: %d' % (repo.html_url, n))
                elif repo.fatal_error():
                    logging.error('(FATAL ERROR) url: %s, current_step: %d' % (repo.html_url, n))
                    logging.error('(FATAL ERROR) error_msg: %s' % repo.error_msg())
                    f.close()
                    sys.exit(0)
                else:
                    valid_n += 1
                    if repos.find_one({ "full_name": repo.full_name }) is None:
                        repos.insert_one(repo.dict())

            n = rlimit

            print "# processed: %d" % valid_n
            print "%d stopwords: %s\n" % (len(Repo.stopwords), Repo.stopwords)

    f.close()
    print "TOTAL NUMBER: %d" % n
    print "TOTAL VALID NUMBER: %d" % valid_n



