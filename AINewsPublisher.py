# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

import feedparser
import sys
import operator
import re
import urllib2
from lxml import etree
from os import path, mkdir, remove
from glob import glob
from random import shuffle
from subprocess import *
from datetime import date, datetime, timedelta
from AINewsTools import savefile, convert_to_printable
from AINewsConfig import config, paths, aitopic_urls, blacklist_urls
from AINewsDB import AINewsDB
from AINewsCorpus import AINewsCorpus
from AINewsDuplicates import AINewsDuplicates
from AINewsSVMClassifier import AINewsSVMClassifier
from AINewsTextProcessor import AINewsTextProcessor
from AINewsSummarizer import AINewsSummarizer

sys.path.append(paths['templates.compiled'])
from FeedImport import FeedImport
from LatestNewsEmail import LatestNewsEmail

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

        self.articles = {}
        self.semiauto_email_output = ""

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
        print "Filtering by date..."
        for urlid in self.articles:
            if self.articles[urlid]['pubdate'] == None:
                # give a meaningful pubdate so that other code doesn't crash
                self.articles[urlid]['pubdate'] = self.today
                self.articles[urlid]['publish'] = False
                self.articles[urlid]['transcript'].append("Rejected due to bogus publication date.")
            elif self.articles[urlid]['pubdate'] < self.earliest_date:
                self.articles[urlid]['publish'] = False
                self.articles[urlid]['transcript'].append(
                        ("Rejected because article is too old " +
                        "(earliest valid date is %s while article was " +
                        "published on %s") % (self.earliest_date.strftime('%F'),
                            self.articles[urlid]['pubdate'].strftime('%F')))

        # filter by blacklist (for urls)
        print "Filtering by blacklist..."
        for urlid in self.articles:
            for black in blacklist_urls:
                if re.search(black, self.articles[urlid]['url']):
                    self.articles[urlid]['publish'] = False
                    self.articles[urlid]['transcript'].append(
                        ("Rejected because url matched blacklisted url %s" % black))
                    break

        # filter by whitelist
        print "Filtering by whitelist..."
        for urlid in self.articles:
            white_wordfreq = self.txtpro.whiteprocess(urlid,
                    self.articles[urlid]['content'])
            self.articles[urlid]['white_wordfreq'] = white_wordfreq

            # require at least two different whitelisted terms
            # unless the article is user-submitted
            if len(white_wordfreq) < 2 \
                    and self.articles[urlid]['source'] != 'User Submitted':
                self.articles[urlid]['publish'] = False
                self.articles[urlid]['transcript'].append(
                        'Rejected due to only one or no whitelisted terms')

        # update categories based on SVM classifier predictions
        print "Classifying..."
        self.svm_classifier.predict(self.articles)

        # drop articles classified as 'NotRelated' unless the article
        # is user-submitted
        for urlid in self.articles:
            if 'NotRelated' in self.articles[urlid]['categories'] \
                    and self.articles[urlid]['source'] != 'User Submitted':
                self.articles[urlid]['publish'] = False
                self.articles[urlid]['transcript'].append(
                        'Rejected due to NotRelated classification')

        # drop articles with no categories (even if user-submitted)
        print "Dropping articles with no categories..."
        for urlid in self.articles:
            if len(self.articles[urlid]['categories']) == 0:
                self.articles[urlid]['publish'] = False
                self.articles[urlid]['transcript'].append(
                        'Rejected due to no selected categories')

        # filter out duplicates; some articles may have 'publish' set to False
        # by this function
        print "Filtering duplicates..."
        self.duplicates.filter_duplicates(self.articles)

        for urlid in self.articles:
            print urlid, self.articles[urlid]['publish'], \
                self.articles[urlid]['title'], \
                self.articles[urlid]['categories'], \
                self.articles[urlid]['summary']
            print

        print "Grabbing images..."
        for urlid in self.articles:
            # grab and convert article image (if it exists)
            self.grab_convert_image(self.articles[urlid])

            # update article in database
            self.update_db(self.articles[urlid])

        # mark each as processed
        print "Marking as processed."
        self.corpus.mark_processed(self.articles.itervalues())

        # save sorted list of articles to be read by AINewsPublisher; sort by
        # duplicate count (more = better), then relevance of source,
        # then by number of categories (more = better)
        unpublished_articles = sorted(
                filter(lambda x: x['publish'], self.articles.values()),
                cmp=lambda x,y: self.corpus.compare_articles(x, y),
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
        self.publishable_articles = []
        for article in unpublished_articles:
            if len(self.publishable_articles) == max_count:
                break
            free_cat = False
            for cat in article['categories']:
                if cat_counts[cat] < max_cat_count:
                    free_cat = True
                    break
            # if there is a free category or this article has only the
            # Applications category, then it can be published
            if free_cat or (article['categories'] == ['Applications']):
                self.publishable_articles.append(article)
                self.articles[article['urlid']]['transcript'].append('Published')
                self.articles[article['urlid']]['published'] = True
                for cat in article['categories']:
                    cat_counts[cat] += 1

        # record that these articles are publishable
        self.corpus.mark_publishable(self.publishable_articles)

    def grab_convert_image(self, article):
        if len(article['image_url']) == 0:
            article['image_path'] = ''
            return
        try:
            f = urllib2.urlopen(article['image_url'])
            img = open("%s%s" % (paths['ainews.image_dir'], str(article['urlid'])), 'w')
            img.write(f.read())
            img.close()
            # produces [urlid].jpg
            Popen("%s -format jpg -gravity Center -thumbnail 200x200 %s%s" % \
                      (paths['imagemagick.mogrify'], paths['ainews.image_dir'], str(article['urlid'])),
                  shell = True).communicate()
            # remove [urlid] file (with no extension)
            remove("%s%s" % (paths['ainews.image_dir'], str(article['urlid'])))
            article['image_path'] = "public://newsfinder_images/%s.jpg" % article['urlid']
        except Exception as e:
            print "Failed converting image for %d: %s" % (article['urlid'], e)
            article['image_path'] = ''

    def update_db(self, article):
        self.db.execute("delete from categories where urlid = %s", article['urlid'])
        for cat in article['categories']:
            self.db.execute("insert into categories values (%s,%s)",
                (article['urlid'], cat))

    def generate_feed_import(self):
        """
        Generate XML file for feed import on the Drupal site.
        """
        xml = FeedImport()
        for article in self.articles.values():
            article['source'] = re.sub(r'&', '&amp;', article['source'])
            cats_fixed = []
            for cat in article['categories']:
                if cat == "Agents": continue
                if cat == "AIOverview":
                    cat = "AI Overview"
                if cat == "CognitiveScience":
                    cat = "Cognitive Science"
                if cat == "Education": continue
                if cat == "Ethics":
                    cat = "Ethics &amp; Social Issues"
                if cat == "Games":
                    cat = "Games &amp; Puzzles"
                if cat == "MachineLearning":
                    cat = "Machine Learning"
                if cat == "NaturalLanguage":
                    cat = "Natural Language"
                if cat == "Reasoning":
                    cat = "Representation &amp; Reasoning"
                if cat == "Representation":
                    cat = "Representation &amp; Reasoning"
                if cat == "ScienceFiction":
                    cat = "Science Fiction"
                if cat == "Systems":
                    cat = "Systems &amp; Languages"
                cats_fixed.append(cat)
            article['categories_fixed'] = cats_fixed
        xml.news = self.articles.values()
        savefile(paths['ainews.output_xml'] + "news.xml", str(xml))
        
    def generate_email_output(self):
        articles = []
        try:
            f = urllib2.urlopen(paths['ainews.top_weekly_news_xml'])
            xml = etree.parse(f)
            for node in xml.iter("node"):
                print "Found", node.findtext("Title")
                published = node.findtext("Publication_date")
                image = ""
                m = re.search(r'(http.*\.jpg)', node.findtext("Representative_image"))
                if m:
                    image = m.group(1)
                articles.append({'title': node.findtext("Title"),
                                 'source': node.findtext("Source"),
                                 'topics': re.sub(r'/topic/', 'http://aitopics.org/topic/', node.findtext("Topics")),
                                 'pubdate': date(int(published[0:4]),
                                                 int(published[5:7]),
                                                 int(published[8:10])),
                                 'summary': node.findtext("Body"),
                                 'url': node.findtext("Original_link"),
                                 'link': 'http://aitopics.org%s' %  node.findtext("Link"),
                                 'image': image})
        except Exception, e:
            print e

        email = LatestNewsEmail()
        email.date = self.today.strftime("%B %d, %Y")
        email.year = self.today.strftime("%Y")
        email.articles = articles
        email_output = str(email)

        return email_output
        
    def publish_email_semiauto(self):
        """
        Create an AINewsSemiAutoEmail.html file for admin to click and semi-auto
        send it to the subscriber list.
        """

        output = self.generate_email_output()

        semiauto = """
        <html>
        <head>
        <META HTTP-EQUIV="Pragma" CONTENT="no-cache">
        <META HTTP-EQUIV="Expires" CONTENT="-1">
        </head>
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
        <h2>Please review the email below. If there are concerns, contact Bruce or Reid:</h2>
        <p>
        %s
        </p>
        </body>
        <head>
        <META HTTP-EQUIV="Pragma" CONTENT="no-cache">
        <META HTTP-EQUIV="Expires" CONTENT="-1">
        </head>
        </html>
        """ % ("AI Alert - "+str(self.today.strftime("%B %d, %Y")), output, output)
        savefile(paths['ainews.html'] + "semiauto_email.html", semiauto)


