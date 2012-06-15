# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.


"""
Crawling major news websites for latest Artificial Intelligence related news
stories.
AINewsCrawler is a major AINewsFinder component which is composed of
AINewsParser, AINewsSourceParser, AINewsTextProcessor, AINewsTopic, AINewsSim,
AINewsDB. It parses HTML news from either website's search page or website's
RSS/Atom feeds, extracts text information, filters unrelated news and finally
stores the bag of words of each news into database.
"""
import os
import sys
import re
import time
import types
import traceback
from datetime import date, timedelta
import string

import ents

from AINewsConfig import config, paths, blacklist_words
from AINewsTools import savefile, loadcsv, strip_html, savepickle, loadfile, trunc
from AINewsParser import AINewsParser
from AINewsSourceParser import *
from AINewsDB import AINewsDB

def convert_to_printable(text):
    result = ""
    for c in text:
        if c in string.printable: result += str(c)
    return result

class AINewsCrawler:
    def __init__(self):
        self.today = date.today()
        self.debug = config['ainews.debug']
        self.db = AINewsDB()
        self.parser = AINewsParser()

    def get_newssources(self, opts):
        """
        Get the news source list.
        """
        sources = []
        where = "1=1"
        for opt in opts:
            if opt[0] == "-s" or opt[0] == "--source":
                where = "id = %s" % opt[1]
        
        sql = "select url,parser,description from sources where status = 1 and %s order by id asc" % where
        rows = self.db.selectall(sql)
        for row in rows:
            items = row[1].split('::')
            sources.append((row[0], items[0], items[1], row[2]))
        return sources

    def crawl(self, opts):
        """
        Crawl the news by source lists (Search page or RSS).
        """
        rows = self.get_newssources(opts)
        for row in rows:
            sourcepage_url = row[0]
            publisher = row[1]
            sourcetype = row[2]
            tag = row[3]
            parser = ParserFactory(publisher, sourcetype)
            if parser == None: continue
            if self.debug: print "Crawling %s (%s):" % (publisher, tag)
            try:
                parser.parse_sourcepage(sourcepage_url)
                parser.parse_storypage()
                for candidate in parser.candidates:
                    if len(candidate) != 4: continue
                    url = candidate[0].encode('utf-8')
                    print "Fetching", url
                    title = convert_to_printable(ents.convert((re.sub(r'\s+', ' ', candidate[1])))).strip()
                    # if publisher is GoogleNews, extract true publisher from title
                    if publisher == "GoogleNews":
                        print title
                        true_publisher = re.match(r'^.* - (.+)$', title).group(1)
                        true_publisher = "%s via Google News" % true_publisher
                    elif publisher == "UserSubmitted":
                        true_publisher = re.match(r'^[^\/]+:\/\/([^\/]+)(?::\d+)?\/?.*$', url).group(1)
                        true_publisher = "%s (User submitted)" % true_publisher
                    else: true_publisher = publisher

                    # removing site title like " - NPR"
                    title = re.sub(r'\s+[:-]\s+.*$', '', title)
                    pubdate = candidate[2]
                    content = convert_to_printable(ents.convert((re.sub(r'\s+', ' ', candidate[3])))).strip()
                    if isinstance(title, types.StringType):
                        title = unicode(title, errors = 'ignore')
                    if isinstance(content, types.StringType):
                        content = unicode(content, errors = 'ignore')
                    content = re.sub("\\s*%s\\s*" % re.escape(title), '', content)
                    content = re.sub(r'\s*Share this\s*', '', content)
                    content = re.sub(r'\s+,\s+', ', ', content)
                    content = re.sub(r'\s+\.', '.', content)

                    if len(title) < 5 or len(content) < 2000:
                        print "Content or title too short"
                        continue

                    # shorten content to (presumably) ignore article comments
                    content = trunc(content, max_pos=3000)

                    # remove content with blacklisted words
                    found_blacklist_word = False
                    for word in blacklist_words:
                        if re.search("\W%s\W" % word, content, re.IGNORECASE) != None:
                            print "Found blacklisted word \"%s\", ignoring article." % word
                            found_blacklist_word = True
                            break
                    if found_blacklist_word: 
                        continue

                    urlid = self.put_in_db(url, pubdate, self.today, true_publisher, \
                            tag, title, content)
                    if urlid == None: continue
                    try:
                        print "{ID:%d} %s (%s, %s)" % (urlid, title, str(pubdate), true_publisher)
                    except:
                        pass

            except (KeyboardInterrupt):
                if self.debug: print "Quitting early due to keyboard interrupt."
                sys.exit()
            except:
                if self.debug:
                    print "Parser for %s failed." % (publisher)
                    print traceback.print_exc()
                continue;

    def put_in_db(self, url, pubdate, crawldate, publisher, tag, title, content):
        """
        Save the news story into database.
        """
        try:
            urlid = self.db.execute("""insert into urllist (url, pubdate, crawldate,
                publisher, tag, title, content)
                values (%s, %s, %s, %s, %s, %s, %s)""",
                (url, str(pubdate), str(crawldate), publisher, tag, title, content))
            return urlid
        except Exception, e :
            #if self.debug:
            #   print >> sys.stderr, "ERROR: can't add url metadata.", e
            return None

