"""
AINewsPublisher generates the ranked latest news into different output format.
It publish to the PmWiki website and send email to subscriber. Facebook page
can be added in the future task.

The pmwiki page utilizes the AINewsPmwiki.php file to transfer the output file
into PmWiki format.
"""
import feedparser
import PyRSS2Gen
import sys
from os import path, mkdir
from glob import glob
from random import shuffle
from subprocess import *
from datetime import date, datetime, timedelta
from operator import itemgetter
from AINewsTools import loadpickle, savefile,savepickle
from AINewsConfig import config, paths, aitopic_urls

sys.path.append(paths['templates.compiled'])
from LatestNewsTxt import LatestNewsTxt
from LatestNewsEmail import LatestNewsEmail
from LatestNewsPmWiki import LatestNewsPmWiki
from ArticlePmWiki import ArticlePmWiki

class AINewsPublisher():
    def __init__(self):
        self.debug = config['ainews.debug']
        self.today = date.today()
        self.topicids = {"AIOverview":0, "Agents":1, "Applications":2,
           "CognitiveScience":3, "Education":4,"Ethics":5, 
           "Games":6, "History":7, "Interfaces":8, "MachineLearning":9,
           "NaturalLanguage":10, "Philosophy":11, "Reasoning":12,
           "Representation":13, "Robots":14, "ScienceFiction":15,"Speech":16,
           "Systems":17,  "Vision":18}

        news_unfiltered = loadpickle(paths['ainews.output'] + "topnews.pkl")
        # filter topnews_unfiltered, moving through each category one at a
        # time, picking a top story in that category until STORIES_COUNT
        # stories are obtained
        stories_count = int(config['publisher.stories_count'])
        topicids = self.topicids.keys()
        self.topnews = []
        for max_count in range(1, stories_count + 1):
            if(len(self.topnews) == stories_count):
                break
            shuffle(topicids)
            for topic in topicids:
                if(len(self.topnews) == stories_count):
                    break
                topic_count = len(filter(lambda n: n['topic'] == topic, self.topnews))
                if(topic_count == max_count):
                    continue
                topic_news = filter(lambda n: n['topic'] == topic, news_unfiltered)
                if(len(topic_news) == 0):
                    continue
                self.topnews.append(topic_news[0])
                news_unfiltered.remove(topic_news[0])

        # sort topnews disregarding topic (sort on score)
        self.topnews = sorted(self.topnews, key=itemgetter('score'), reverse=True)
        
        currmonth = self.today.strftime("%Y-%m")
        p = paths['ainews.output'] + "monthly/" + currmonth
        if not path.exists(p):
            mkdir(p)
        savepickle(p+"/"+self.today.strftime("%d"), self.topnews)
        
        self.semiauto_email_output = ""
        
    def generate_standard_output(self): 
        """
        Generate the stanard output for debuging on screen.
        """
        txt = LatestNewsTxt()
        txt.news = self.topnews
        savefile(paths['ainews.output'] + "std_output.txt", str(txt))
        
    
    def generate_email_output(self):
        """
        Generate the output for email format.
        """
        email = LatestNewsEmail()
        email.date = self.today.strftime("%B %d, %Y")
        email.news = self.topnews
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
        pmwiki.news = self.topnews
        pmwiki.rater = True
        savefile(paths['ainews.output'] + "pmwiki_output.txt", str(pmwiki))
        pmwiki.rater = False
        savefile(paths['ainews.output'] + "pmwiki_output_norater.txt", str(pmwiki))

        # Generate wiki metadata page for each article
        urlids_output = ""
        for news in self.topnews:
            urlids_output += str(news['urlid']) + '\n'
            article = ArticlePmWiki()
            article.n = news
            savefile(paths['ainews.output'] + "aiarticles/%d" % news['urlid'], str(article))

        savefile(paths['ainews.output'] + "urlids_output.txt", urlids_output)

    def publish_email(self):
        """
        Call AINewsEmail.php to send email through PHP Mail Server
        """
        cmd = 'php AINewsEmail.php'
        Popen(cmd, shell = True, stdout = PIPE, stderr = STDOUT).communicate()
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
        Popen(cmd, shell = True, stdout = PIPE).communicate()
        
    def update_rss(self):
        rssitems = []
        # insert latest news into rssitems
        for news in self.topnews:
            rssitems.append(PyRSS2Gen.RSSItem(
                            title = news['title'],
                            link = news['url'],
                            description = news['desc'],
                            guid = PyRSS2Gen.Guid(news['url']),
                            pubDate = datetime(news['pubdate'].year, \
                                news['pubdate'].month, news['pubdate'].day)
                            ))
            
        rssfile = paths['ainews.rss'] + "news.xml"
        publish_rss(rssfile, rssitems)
        
        
        topicrsses = ['overview', 'agent', 'apps', 'cogsci', 'edu', 'ethsoc', 
            'game', 'hist', 'interf', 'ml', 'nlp', 'phil', 'reason',
             'rep', 'robot', 'scifi', 'speech', 'systems',  'vision']
        topicitems = []
        for i in range(len(topicrsses)): topicitems.append([])
        for news in self.topnews:
            topicid = self.topicids[news['topic']]
            topicitems[topicid].append(PyRSS2Gen.RSSItem(
                                title = news['title'],
                                link = news['url'],
                                description = news['desc'],
                                guid = PyRSS2Gen.Guid(news['url']),
                                pubDate = datetime(news['pubdate'].year, \
                                    news['pubdate'].month, news['pubdate'].day)
                                ))
            
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

