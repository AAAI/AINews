# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

import os
import sys
import re
import feedparser
import cgi
from subprocess import *
from datetime import date, timedelta
import string
import csv
import urllib2

from AINewsConfig import config, paths, blacklist_words
from AINewsTools import savefile, loadcsv, strip_html, savepickle, loadfile, trunc, convert_to_printable
from AINewsDB import AINewsDB
from AINewsSummarizer import AINewsSummarizer

class AINewsCrawler:
    def __init__(self):
        self.today = date.today()
        self.earliest_date = self.today - timedelta(days = int(config['ainews.period']))
        self.db = AINewsDB()
        self.summarizer = AINewsSummarizer()
        self.articles = []

    def get_sources(self):
        """
        Get the news source list.
        """
        sources = []
        csv_file = csv.reader(urllib2.urlopen(paths['ainews.sources_csv']))
        header = True
        for row in csv_file:
            if header:
                header = False
                continue
            sources.append({'source_id': row[0],
                            'title': row[1],
                            'link': row[2],
                            'parser': row[3],
                            'relevance': int(row[4])})
        return sources

    def fetch_all_sources(self):
        for source in self.get_sources():
            print "CRAWL: Crawling \"%s\"..." % source['title']
            f = feedparser.parse(source['link'])
            for entry in f.entries:
                d = None
                try:
                    d = date(entry.published_parsed[0], entry.published_parsed[1], entry.published_parsed[2])
                except:
                    d = self.today
                if d > self.today or d < self.earliest_date: continue
                if entry.title[-6:] == '(blog)' \
                        or entry.title[-15:] == '(press release)': continue

                try:
                    url = urllib2.urlopen(entry.link).geturl()
                except KeyboardInterrupt:
                    print "Quitting early due to keyboard interrupt."
                    sys.exit()
                except: continue

                # attempt to skip blogs
                if re.match('^.*blog.*$', url):
                    continue
                if self.db.crawled(url):
                    continue
                
                title = cgi.escape(convert_to_printable(entry.title)).strip()

                # if source is GoogleNews, extract true source from title
                if re.match(r'^.*Google News.*$', source['title']):
                    true_source = re.match(r'^.* - (.+)$', title).group(1)
                    true_source = "%s via Google News" % true_source
                    title = re.sub(" - %s" % re.escape(true_source), '', title)
                elif source['title'] == "User Submitted":
                    true_source = re.match(r'^[^\/]+:\/\/([^\/]+)(?::\d+)?\/?.*$', url).group(1)
                    true_source = "%s (User submitted)" % true_source
                else: true_source = source['title']
                
                self.articles.append({'url': url, 'title': title, 'pubdate': d,
                                      'source': true_source, 'source_id': source['source_id'],
                                      'source_relevance': source['relevance']})

    def fetch_all_articles(self):
        f = open("%surllist.txt" % paths['ainews.content_tmp'], 'w')
        for article in self.articles:
            f.write("%s\n" % article['url'])
        f.close()

        goose_cmd = "cd %s/goose; MAVEN_OPTS=\"-Xms256m -Xmx800m\" %s exec:java -Dexec.mainClass=com.gravity.goose.FetchMany -Dexec.args=\"%s\" -q" % (paths['libraries.tools'], paths['libraries.maven'], paths['ainews.content_tmp'])
        Popen(goose_cmd, shell = True).communicate()

        i = 0
        for article in self.articles:
            if self.db.crawled(article['url']):
                continue
            f = open("%s%d" % (paths['ainews.content_tmp'], i))
            i += 1
            rows = f.read().split("\n")
            f.close()

            if len(rows) < 3:
                print "FETCH: .. Ignoring; not enough lines in Goose output: URL=%s, ROWS=%s" % (article['url'], rows)
                continue

            self.db.set_crawled(article['url'])
            content = ' '.join(rows[:-2])
            content = convert_to_printable(cgi.escape(re.sub(r'\s+', ' ', content))).strip()
            content = re.sub("%s\\s*-?\\s*" % re.escape(article['title']), '', content)
            content = re.sub(r'\s*Share this\s*', '', content)
            content = re.sub(r'\s+,\s+', ', ', content)
            content = re.sub(r'\s+\.', '.', content)
            # shorten content to (presumably) ignore article comments
            content = trunc(content, max_pos=3000)
            article['content'] = content

            print "SUMRY: ..", article['title']
            article['summary'] = self.summarizer.summarize_single_ots(article['content'])
            article['image_url'] = convert_to_printable(rows[-2]).strip()

            if len(article['title']) < 5 or len(article['content']) < 1000:
                print "CRAWL: -- Ignoring. Content or title too short. Title = {%s}; Content = {%s}" % \
                    (article['title'], article['content'])
                continue

            # remove content with blacklisted words
            found_blacklist_word = False
            for word in blacklist_words:
                if re.search("\W%s\W" % word, article['content'], re.IGNORECASE) != None:
                    print "CRAWL: -- Ignoring. Found blacklisted word \"%s\", ignoring article." % word
                    found_blacklist_word = True
                    break
            if found_blacklist_word: 
                continue

            urlid = self.put_in_db(article)
            if urlid == None: continue
            try:
                print "CRAWL: ++ {ID:%d} %s (%s, %s)" % \
                    (urlid, article['title'], str(article['pubdate']), article['source'])
            except:
                pass

    def put_in_db(self, article):
        """
        Save the article into the database.
        """
        try:
            urlid = self.db.execute("""insert into urllist (url, pubdate, crawldate,
                source, source_id, source_relevance, title, content, summary, image_url)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (article['url'], str(article['pubdate']), str(self.today),
                 article['source'], article['source_id'], article['source_relevance'],
                 article['title'], article['content'], article['summary'], article['image_url']))
            return urlid
        except KeyboardInterrupt:
            print "Quitting early due to keyboard interrupt."
            sys.exit()
        except Exception, e:
            print "ERROR: can't add article to db:", e
            return None

