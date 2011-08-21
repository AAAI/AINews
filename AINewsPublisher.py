# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

import feedparser
import PyRSS2Gen
import sys
import operator
from os import path, mkdir
from glob import glob
from random import shuffle
from subprocess import *
from datetime import date, datetime, timedelta
from AINewsTools import savefile
from AINewsConfig import config, paths, aitopic_urls
from AINewsDB import AINewsDB
from AINewsCorpus import AINewsCorpus
from AINewsDuplicates import AINewsDuplicates
from AINewsSVMClassifier import AINewsSVMClassifier
from AINewsTextProcessor import AINewsTextProcessor
from AINewsSummarizer import AINewsSummarizer

sys.path.append(paths['templates.compiled'])
from LatestNewsTxt import LatestNewsTxt
from LatestNewsEmail import LatestNewsEmail
from LatestNewsPmWiki import LatestNewsPmWiki
from ArticlePmWiki import ArticlePmWiki
from AllNewsPmWiki import AllNewsPmWiki

class AINewsPublisher():
    def __init__(self):
        self.debug = config['ainews.debug']
        self.today = date.today()
        self.earliest_date = self.today - timedelta(days = int(config['ainews.period']))
        self.db = AINewsDB()
        self.corpus = AINewsCorpus()
        self.duplicates = AINewsDuplicates()
        self.svm_classifier = AINewsSVMClassifier()
        self.txtpro = AINewsTextProcessor()
        self.summarizer = AINewsSummarizer()

        self.sources = {}
        rows = self.db.selectall("select parser, relevance from sources")
        for row in rows:
            self.sources[row[0].split('::')[0]] = int(row[1])

        self.articles = {}
        self.published_articles = []

        self.topicids = {"AIOverview":0, "Agents":1, "Applications":2,
           "CognitiveScience":3, "Education":4,"Ethics":5, 
           "Games":6, "History":7, "Interfaces":8, "MachineLearning":9,
           "NaturalLanguage":10, "Philosophy":11, "Reasoning":12,
           "Representation":13, "Robots":14, "ScienceFiction":15,"Speech":16,
           "Systems":17,  "Vision":18}

    def filter_and_process(self):
        self.articles = self.corpus.get_unprocessed()

        if len(self.articles) == 0: return

        # assume every article will be published; may be set to False from one
        # of the filtering processes below
        for urlid in self.articles:
            self.articles[urlid]['publish'] = True
            self.articles[urlid]['transcript'] = []

        # filter by date
        for urlid in self.articles:
            if self.articles[urlid]['pubdate'] < self.earliest_date:
                self.articles[urlid]['publish'] = False
                self.articles[urlid]['transcript'].append(
                        ("Rejected because article is too old " +
                        "(earliest valid date is %s while article was " +
                        "published on %s") % (self.earliest_date.strftime('%F'),
                            self.articles[urlid]['pubdate'].strftime('%F')))

        # filter by whitelist
        for urlid in self.articles:
            white_wordfreq = self.txtpro.whiteprocess(urlid,
                    self.articles[urlid]['content'])
            self.articles[urlid]['white_wordfreq'] = white_wordfreq

            # require at least two different whitelisted terms
            # unless the article is user-submitted
            if len(white_wordfreq) < 2 \
                    and self.articles[urlid]['publisher'] != 'UserSubmitted':
                self.articles[urlid]['publish'] = False
                self.articles[urlid]['transcript'].append(
                        'Rejected due to only one or no whitelisted terms')

        # update categories based on SVM classifier predictions
        self.svm_classifier.predict(self.articles)

        # drop articles classified as 'NotRelated' unless the article
        # is user-submitted
        for urlid in self.articles:
            if 'NotRelated' in self.articles[urlid]['categories'] \
                    and self.articles[urlid]['publisher'] != 'UserSubmitted':
                self.articles[urlid]['publish'] = False
                self.articles[urlid]['transcript'].append(
                        'Rejected due to NotRelated classification')

        # drop articles with no categories (even if user-submitted)
        for urlid in self.articles:
            if len(self.articles[urlid]['categories']) == 0:
                self.articles[urlid]['publish'] = False
                self.articles[urlid]['transcript'].append(
                        'Rejected due to no selected categories')

        for urlid in self.articles:
            # update article in database
            self.update_db(self.articles[urlid])

        # filter out duplicates; some articles may have 'publish' set to False
        # by this function
        self.duplicates.filter_duplicates(self.articles, self.sources)

        # add article summaries
        self.summarizer.summarize(self.corpus, self.articles)

        for urlid in self.articles:
            try:
                print urlid, self.articles[urlid]['publish'], \
                    self.articles[urlid]['title'], \
                    self.articles[urlid]['categories'], \
                    self.articles[urlid]['summary']
                print
            except:
                pass

        # mark each as processed
        self.corpus.mark_processed(self.articles)


        # save sorted list of articles to be read by AINewsPublisher; sort by
        # duplicate count (more = better), then relevance of source,
        # then by number of categories (more = better)
        unpublished_articles = sorted(
                filter(lambda x: x['publish'], self.articles.values()),
                cmp=lambda x,y: self.compare_articles(x, y),
                reverse = True)

        max_cat_count = int(config['publisher.max_cat_count'])
        max_count = int(config['publisher.max_count'])
        cat_counts = {}
        for cat in self.corpus.categories:
            cat_counts[cat] = 0
        # choose stories such that no category has more than max_cat_count
        # members and no more than max_count stories have been selected
        # (independent of category); only one of the article's categories needs
        # to have "free space"
        self.published_articles = []
        for article in unpublished_articles:
            if len(self.published_articles) == max_count:
                break
            free_cat = False
            for cat in article['categories']:
                if cat_counts[cat] < max_cat_count:
                    free_cat = True
                    break
            if free_cat:
                self.published_articles.append(article)
                self.articles[article['urlid']]['transcript'].append('Published')
                self.articles[article['urlid']]['published'] = True
                for cat in article['categories']:
                    cat_counts[cat] += 1

        # update published articles in db
        self.corpus.mark_published(self.published_articles)

        self.semiauto_email_output = ""

    def compare_articles(self, article1, article2):
        dupcount1 = len(article1['duplicates'])
        dupcount2 = len(article2['duplicates'])
        relevance1 = self.sources[article1['publisher']]
        relevance2 = self.sources[article2['publisher']]
        cat_count1 = len(article1['categories'])
        cat_count2 = len(article2['categories'])
        if cmp(dupcount1, dupcount2) == 0:
            if cmp(relevance1, relevance2) == 0:
                return cmp(cat_count1, cat_count2)
            else:
                return cmp(relevance1, relevance2)
        else:
            return cmp(dupcount1, dupcount2)

    def update_db(self, article):
        self.db.execute("delete from categories where urlid = %s", article['urlid'])
        for cat in article['categories']:
            self.db.execute("insert into categories values (%s,%s)",
                (article['urlid'], cat))

    def generate_standard_output(self): 
        """
        Generate the stanard output for debuging on screen.
        """
        txt = LatestNewsTxt()
        txt.news = self.published_articles
        savefile(paths['ainews.output'] + "std_output.txt", str(txt))

    def generate_email_output(self):
        """
        Generate the output for email format.
        """
        email = LatestNewsEmail()
        email.date = self.today.strftime("%B %d, %Y")
        email.news = self.published_articles
        email.aitopic_urls = aitopic_urls
        email.topicids = self.topicids
        email_output = str(email)

        savefile(paths['ainews.output'] + "email_output.txt", email_output)
        self.semiauto_email_output = email_output
        
    def generate_pmwiki_output(self):
        """
        Genereate the output with PmWiki page format. It needs to be further
        processed by AINewsPmwiki.php.
        """
        pmwiki = LatestNewsPmWiki()
        pmwiki.date = self.today.strftime("%B %d, %Y")
        pmwiki.year = self.today.strftime("%Y")
        pmwiki.news = self.published_articles
        pmwiki.rater = True
        savefile(paths['ainews.output'] + "pmwiki_output.txt", str(pmwiki))
        pmwiki.rater = False
        savefile(paths['ainews.output'] + "pmwiki_output_norater.txt", str(pmwiki))

        pmwiki_all = AllNewsPmWiki()
        pmwiki_all.date = self.today.strftime("%B %d, %Y")
        pmwiki_all.year = self.today.strftime("%Y")
        pmwiki_all.news = self.articles.values()
        savefile(paths['ainews.output'] + "pmwiki_all.txt", str(pmwiki_all))

        # Generate wiki metadata page for each article
        urlids_output = ""
        for urlid in self.articles:
            urlids_output += str(urlid) + '\n'
            article_wiki = ArticlePmWiki()
            article_wiki.year = self.today.strftime("%Y")
            article_wiki.dupthreshold = float(config['duplicates.threshold'])
            article_wiki.n = self.articles[urlid]
            savefile(paths['ainews.output'] + "aiarticles/%d" % urlid,
                    str(article_wiki))
        savefile(paths['ainews.output'] + "urlids_output.txt", urlids_output)


    def publish_email(self):
        """
        Call AINewsEmail.php to send email through PHP Mail Server
        """
        #cmd = 'php AINewsEmail.php'
        #Popen(cmd, shell = True, stdout = PIPE, stderr = STDOUT).communicate()
        self.publish_email_semiauto()
        
    def publish_email_semiauto(self):
        """
        Create an AINewsSemiAutoEmail.html file for admin to click and semi-auto
        send it to the subscriber list.
        """
        semiauto = """
        <html>
        <body>
        <h1>AI Alert - SemiAuto Sender</h1>
        <form action="http://aaai.org/cgi-dada/mail.cgi?flavor=send_email" method='post'>
        <!-- <form action="welcome.php" method="post"> -->
        <input type='hidden' name='f' value='send_email' />
        <input type='hidden' name='process' value='true' />
        <input type='hidden' name='admin_list' value='alert' />
        <input type='hidden' name='message_subject' value="%s" />
        <input type='hidden' name='email_format' value='HTML' />
        <textarea type='hidden' name="text_message_body">%s</textarea>
        <input type='submit' value='Submit Mailing List Message' />
        </form>
        </body>
        </html>
        """ % ("AI Alert - "+str(self.today.strftime("%B %d, %Y")), self.semiauto_email_output)
        savefile(paths['ainews.html'] + "semiauto_email.html", semiauto)

    def publish_pmwiki(self):
        """
        Call AINewsPmwiki.php to publish latest news to AAAI Pmwiki website.
        """
        cmd = 'php AINewsPmwiki.php'
        Popen(cmd, shell = True).wait()
        
    def update_rss(self):
        rssitems = []
        # insert latest news into rssitems
        for article in self.published_articles:
            rssitems.append(PyRSS2Gen.RSSItem(
                title = article['title'],
                link = article['url'],
                description = article['summary'],
                guid = PyRSS2Gen.Guid(article['url']),
                pubDate = datetime(article['pubdate'].year, \
                    article['pubdate'].month, article['pubdate'].day)))
            
        rssfile = paths['ainews.rss'] + "news.xml"
        publish_rss(rssfile, rssitems)
        
        
        topicrsses = ['overview', 'agent', 'apps', 'cogsci', 'edu', 'ethsoc', 
            'game', 'hist', 'interf', 'ml', 'nlp', 'phil', 'reason',
             'rep', 'robot', 'scifi', 'speech', 'systems',  'vision']
        topicitems = []
        for i in range(len(topicrsses)):
            topicitems.append([])
        for article in self.published_articles:
            for cat in article['categories']:
                topicid = self.topicids[cat]
                topicitems[topicid].append(PyRSS2Gen.RSSItem(
                        title = article['title'],
                        link = article['url'],
                        description = article['summary'],
                        guid = PyRSS2Gen.Guid(article['url']),
                        pubDate = datetime(article['pubdate'].year, \
                            article['pubdate'].month, article['pubdate'].day)))
            
        for i in range(len(topicrsses)):
            rssfile = paths['ainews.rss'] + topicrsses[i]+'.xml'
            if len(topicitems[i]) != 0:
                publish_rss(rssfile, topicitems[i])
        
    
def publish_rss(rssfile, rssitems):
    now = datetime.now()
    rss_begindate = now - timedelta(days = 60)
    
    f = feedparser.parse(rssfile)
    urlset = set(map(lambda e: e.link, rssitems))

    # remove out-of-date news and add rest of the news into rssitems
    for entry in f.entries:
        if not entry.has_key('updated_parsed'): continue
        d = datetime(entry.date_parsed[0], \
                       entry.date_parsed[1], entry.date_parsed[2])
        if d > now or d < rss_begindate: continue
        if entry.link in urlset: continue
        urlset.add(entry.link)
        rssitems.append( PyRSS2Gen.RSSItem(
                        title = entry.title,
                        link = entry.link,
                        description = entry.description,
                        guid = PyRSS2Gen.Guid(entry.link),
                        pubDate = d))

    rssitems = sorted(rssitems, key=lambda e: e.pubDate, reverse=True)
    
    # Use PyRSS2Gen to generate the output RSS    
    rss = PyRSS2Gen.RSS2(
        title = f.channel.title,
        link = f.channel.link,
        description = f.channel.description,
        lastBuildDate = now,
        language = 'en-us',
        webMaster = "aitopics08@aaai.org (AI Topics)",
        items = rssitems)
    
    rss.write_xml(open(rssfile, "w"))

