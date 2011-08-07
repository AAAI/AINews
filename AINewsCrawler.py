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

from AINewsConfig import config, paths
from AINewsTools import savefile, loadcsv, strip_html, savepickle, loadfile, trunc
from AINewsParser import AINewsParser
from AINewsSourceParser import *
from AINewsDB import AINewsDB

class AINewsCrawler:
    def __init__(self):
        self.today = date.today()
        self.debug = config['ainews.debug']
        self.db = AINewsDB()
        self.parser = AINewsParser()

    def get_newssources(self):
        """
        Get the news source list.
        """
        sources = []
        sql = "select url,parser,description from sources where status = 1"
        rows = self.db.selectall(sql)
        for row in rows:
            items = row[1].split('::')
            sources.append((row[0], items[0], items[1], row[2]))
        return sources
        
    def crawl(self):
        """
        Crawl the news by source lists (Search page or RSS).
        """
        rows = self.get_newssources()
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
                    title = (re.sub(r'\s+', ' ', candidate[1])).strip()
                    pubdate = candidate[2]
                    content = (re.sub(r'\s+', ' ', candidate[3])).strip()
                    if isinstance(title, types.StringType):
                        title = unicode(title, errors = 'ignore')
                    if isinstance(content, types.StringType):
                        content = unicode(content, errors = 'ignore')

                    if len(title) < 5 or len(content) < 2000: continue

                    urlid = self.put_in_db(url, pubdate, self.today, publisher, \
                            tag, title, content)
                    if urlid == None: continue
                    try:
                        print "{ID:%d} %s (%s)" % (urlid, title, str(pubdate))
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

