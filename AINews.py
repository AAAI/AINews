# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

import sys
import os
import getopt
import locale

from AINewsConfig import config, paths
from AINewsCrawler import AINewsCrawler
from AINewsPublisher import AINewsPublisher
from AINewsWekaClassifier import AINewsWekaClassifier

def usage():
    """
    Print out the command-line usage of AINews.py.
    """
    usage = """                NewsFinder
    USAGE:
        python AINews.py COMMAND [OPTION]
    COMMAND:
        (1) crawl:
            Crawl latest news from outside web.

        (2) prepare:
            Filter and process the news, and create an XML export.

        (3) email:
            Generate an email form for submitting the weekly alert.

        (4) train:
            Update the classifier models.
        """

    print usage
    
def crawl(opts):
    crawler = AINewsCrawler()
    crawler.fetch_all_sources(opts)
    crawler.fetch_all_articles()

def prepare():
    publisher = AINewsPublisher()
    publisher.filter_and_process()
    publisher.generate_feed_import()

def email():
    publisher = AINewsPublisher()
    publisher.publish_email_semiauto()

def train():
    weka = AINewsWekaClassifier()
    weka.train()

def main():
    # Set en_US, UTF8
    locale.setlocale(locale.LC_ALL,'en_US.UTF-8')

    commands_list = ("crawl", "prepare", "email", "train", "help")
    try:
        if len(sys.argv) < 2 or sys.argv[1] not in commands_list:
            usage()
            sys.exit()
        command = sys.argv[1]
        opts, args = getopt.getopt(sys.argv[2:], 'rf:u:s:',
                                   ['url=', 'file=', 'rss', 'source='])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    if command == "crawl":
        crawl(opts)

    elif command == "prepare":
        prepare()

    elif command == "email":
        email()

    elif command == "train":
        train()

if __name__ == "__main__":
    main()
