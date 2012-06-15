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

def usage():
    """
    Print out the command-line usage of AINews.py.
    """
    usage = """                AINews Finder 
    USAGE:
        python AINews.py COMMAND [OPTION]
    COMMAND:
        (1) crawl:
            crawl latest news from outside web.

        (2) train:
            train news classifiers based on human rates.
            
        (3) publish:
            publish news from output files to Pmwiki site and send emails.
            It is weekly publish to the public.
            
        View Latest news at:
        http://www.aaai.org/AITopics/AINews
            
        """

    print usage
    
    
def crawl(opts):
    crawler = AINewsCrawler()
    crawler.crawl(opts)

def train():
    svm = AINewsSVM()
    svm.collect_feedback()
    svm.load_news_words()
    svm.train_all()
    svm.train_isrelated()

def prepare():
    publisher = AINewsPublisher()
    publisher.filter_and_process()
    publisher.generate_pmwiki_all_output()

def publish():
    publisher = AINewsPublisher()
    publisher.get_publishable_articles()
    publisher.generate_standard_output()
    publisher.generate_email_output()
    publisher.generate_pmwiki_published_output()
    publisher.publish_email()
    publisher.publish_pmwiki()
    publisher.update_rss()
    publisher.mark_published()

def main():
    """
    Main function of AINews.py
    """
    # Set en_US, UTF8
    locale.setlocale(locale.LC_ALL,'en_US.UTF-8')

    commands_list = ("train", "crawl", "prepare", "publish", "help")
    try:
        if len(sys.argv) < 2 or sys.argv[1] not in commands_list:
            usage()
            sys.exit()
        command = sys.argv[1]
        opts, args = getopt.getopt(sys.argv[2:], 'rf:u:s:', ['url=', 'file=', 'rss', 'source='])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    if command == "train":
        train()

    elif command == "crawl":
        crawl(opts)

    elif command == "prepare":
        prepare()

    elif command == "publish":
        publish()

if __name__ == "__main__":
    main()

