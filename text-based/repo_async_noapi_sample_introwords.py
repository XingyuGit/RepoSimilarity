import re
from lxml import html
from lxml.html.clean import Cleaner
import eventlet
from eventlet.green import urllib2
import logging
import sys
import time
import random

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class Repo(object):

    ignorewords = set([line.strip('\n').strip() for line in open('stop-words.txt')])
    introwords = {}

    nonalpha_re = re.compile(r"[^a-zA-Z'-]")
    url_re = re.compile(r"http(s?):\/\/\S*")

    # ---- introwords ----

    def add_introwords(self, text):
        if text:
            new_introwords = set(text.split()).difference(self.ignorewords)
            new_introwords = [word for word in new_introwords if len(word) > 2]
            for word in new_introwords:
                self.introwords.setdefault(word, 0)
                self.introwords[word] += 1

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

    # -----------------

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
                self.learn_introwords()
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

    def learn_introwords(self):
        req = urllib2.Request(self.html_url, headers={'Host':'github.com', 'Referer':'https://github.com',
'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36'})
        r = urllib2.urlopen(req)
        page = r.read()
        tree = html.fromstring(page)

        # get readme part
        readme_tree = tree.xpath('//*[@id="readme"]/article')
        if len(readme_tree) < 1:
            return

        readme_tree = readme_tree[0]
        self.origin_readme = readme_tree.text_content()
        cleaner = Cleaner(allow_tags=['p','h1','h2','h3','h4','h5','pre'], remove_unknown_tags=False)
        readme_tree = cleaner.clean_html(readme_tree)

        header = ""
        i = 0

        # iterate each header and paragraph
        for sub in readme_tree.iterchildren():
            if sub is None:
                return

            if i >= 2 or sub.tag == 'pre':
                return

            if sub.tag in ['h1','h2','h3'] and sub.text is not None:
                if header:
                    self.add_introwords(self.filter_all(header))
                    return

                header = sub.text.strip().lower()
                i += 1

        if header:
            self.add_introwords(self.filter_all(header))


fullname_re = re.compile(r'http(s?)://github.com/(.*)')
def fullname_from_url(url):
    return fullname_re.search(url).group(2)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    else:
        n = 0

    valid_n = 0

    pool = eventlet.GreenPool()

    with open('all_repos_refined.csv') as f:
        print "Start getting repo list..."

        all_urls = f.read().splitlines()
        all_urls = all_urls[1:] # get rid of header line

        print "Total length: %d" % len(all_urls)

        random.shuffle(all_urls)
        sample_length = len(all_urls) / 10
        all_urls = all_urls[:sample_length]
        total_length = len(all_urls)

        print "Sample length: %d" % total_length

        print "Repo list ready."

        i = 0
        period = 0
        t = time.clock()
        step = 100

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
                    # f.close()
                    # sys.exit(0)
                else:
                    valid_n += 1

            n = rlimit
            i += 1

            if i == 1:
                period = time.clock() - t
            elif i <= 3:
                period = 0.5 * period + 0.5 * (time.clock() - t)
            else:
                alpha = 0.125
                period = (1 - alpha) * period + alpha * (time.clock() - t)

            t = time.clock()

            print "-------------------------"
            print "# raw introwords: %d" % len(Repo.introwords)
            sw = [word for word in Repo.introwords if Repo.introwords[word] >= 100]
            print "%d refined introwords: %s\n" % (len(sw), sw)

            print "%% processd: %f%%" % (float(n) / total_length * 100)
            print "# validly processed: %d" % valid_n
            print "Approximate remaining time: %f minutes (%f hours)" % \
                  (period * (total_length - n) / step / 60, period * (total_length - n) / step / 3600)
            print "-------------------------\n"

        f.close()
        print "TOTAL NUMBER: %d" % n
        print "TOTAL VALID NUMBER: %d" % valid_n

        with open('my_introwords_limit10.txt', 'w') as swf:
            sw10 = [word for word in Repo.introwords if Repo.introwords[word] >= 10]
            for word in sw10:
                swf.write("%s\n" % word)
            swf.close()

        with open('my_introwords_limit100.txt', 'w') as swf:
            sw100 = [word for word in Repo.introwords if Repo.introwords[word] >= 100]
            for word in sw100:
                swf.write("%s\n" % word)
            swf.close()


