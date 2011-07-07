"""
AINewsSubmitNews.py is used for adding news not by crawling, but by admin's
manually added via Pmwiki pages:
http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/SubmitNewContent

I add codes in the cookbook/articlemailform.php to save the content
into an xml file in aaai/output/submit_news.xml.

This python file process the submit_news.xml and save contents into data base.
"""

import os
import sys
import re
import time
import types
import getopt
import locale
from datetime import date, timedelta

from AINewsConfig import config, paths, \
     whitelist_bigrams, whitelist_unigrams, whitelist_trigrams, \
     dateformat_regexps
from AINewsTools import savefile, loadcsv, strip_html, savepickle, loadfile2
from AINewsTextProcessor import AINewsTextProcessor
from AINewsDB import AINewsDB
from AINewsCentroidClassifier import AINewsCentroidClassifier
from BeautifulSoup import BeautifulSoup, Comment, BeautifulStoneSoup, \
        NavigableString, Declaration, ProcessingInstruction
from AINewsParser import AINewsParser

locale.setlocale(locale.LC_ALL,'en_US.UTF-8')

class AINewsSubmitNews:
    def __init__(self):
        self.today = date.today()
        self.db = AINewsDB()
        self.parser = AINewsParser()
        self.textprocessor = AINewsTextProcessor()
        self.debug = config['ainews.debug']
        self.topic_map = {"aioverview":"AIOverview",
                          "agents":"Agents",
                          "applications":"Applications",
                          "cognitivescience":"CognitiveScience",
                          "education":"Education",
                          "ethicalandsocialimplications":"Ethics",
                          "gamesandpuzzles":"Games",
                          "history":"History",
                          "interfaces":"Interfaces",
                          "machinelearning":"MachineLearning",
                          "naturallanguage":"NaturalLanguage",
                          "philosophy":"Philosophy",
                          "reasoning":"Reasoning",
                          "representation":"Representation",
                          "robots":"Robots",
                          "sciencefiction":"ScienceFiction",
                          "speech":"Speech",
                          "systemsandlanguages":"Systems",
                          "vision":"Vision"
                          }
    
    def process(self, xmlfile):
        print "Processing user submitted news ..."
        xmlcontent = loadfile2(xmlfile)
        xmlcontent = unicode(xmlcontent, errors = 'ignore')
        try:
            xmlsoup = BeautifulSoup(xmlcontent, \
                        convertEntities = BeautifulStoneSoup.HTML_ENTITIES)
        except Exception, error:
            #if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        
        souplist = xmlsoup.findAll('news')
        for soup in souplist:
            type = self.parser.extract_genenraltext(soup.find('type'))
            if type != "NewArticle":
                return
            
            title = self.parser.extract_genenraltext(soup.find('title'))
            url  = self.parser.extract_genenraltext(soup.find('url'))
            date_str   = self.parser.extract_genenraltext(soup.find('date'))
            desc = self.parser.extract_genenraltext(soup.find('description'))
            publisher = self.parser.extract_genenraltext(soup.find('source'))
            topic  = self.parser.extract_genenraltext(soup.find('topic'))
            contributor = self.parser.extract_genenraltext(soup.find('contributor'))
            tags = self.parser.extract_genenraltext(soup.find('tags'))
            
            pub_date = self.extract_date(date_str)
            wordfreq=self.textprocessor.simpletextprocess(desc)
            #desc = desc.encode(encoding='utf-8',errors='ignore')
            #title = title.encode(encoding='utf-8', errors='ignore')
            
            '''
            print title
            print url
            print pub_date
            print desc
            print publisher
            print topic
            print contributor
            print tags
            '''
            
            if topic != "":
                topic = self.topic_map[topic]
            urlid = self.add_urlmeta(url, len(wordfreq), tags, \
                            topic, pub_date, self.today, publisher, title, desc)
            if urlid == None: continue
            self.add_freq_index(wordfreq, 'textwordurl', 'dftext', urlid)
              
            if topic == "":
                model_dir = paths['ainews.category_data'] + "centroid/"
                self.classifier = AINewsCentroidClassifier()
                self.classifier.init_predict(model_dir)
                topic = self.classifier.predict(urlid)
                sql = "update urllist set topic = '%s' where rowid = %d" \
                            % (topic, urlid)
                self.db.execute(sql)
            
             # Save to file
            self.save(urlid, url, str(pub_date), title, desc, desc)
            
            try:
                    print """*{ID:%d} %s (%s - %s)\n\t%s\n\t%s\n\n""" % \
                        (urlid, title, str(pub_date), topic, url, desc )
            except UnicodeError:
                    pass
                
        
        # empty file
        xmlhead = """<?xml version="1.0" encoding="UTF-8"?>
<newslist>
</newslist>"""
        savefile(xmlfile, xmlhead)
  
    def extract_date(self, text):
        """
        Given a text, it tries all the dateformat and expect to extract the
        first matching date from the text.
        @param text: Target text
        @type text: C{string}
        """
        today = date.today()
        for dateformat in dateformat_regexps:
            regexp = dateformat_regexps[dateformat][0]
            res = re.search(regexp, text, re.IGNORECASE)
            if res == None:
                continue
            else:
                date_str = res.group(0)
                t = time.strptime(date_str,dateformat_regexps[dateformat][1])
                d = date(t[0], t[1], t[2])
                if d > today: continue
                else:return d
        return None


    def add_urlmeta(self, url, textlen, tag, topic, pubdate, crawldate, \
                    publisher, title, desc):
        """
        Save the metadata of news story into database.
        """
        url = re.escape(url.encode('utf-8'))
        title = re.escape(title)
        desc = re.escape(desc)
        sql = """ insert into urllist (url, textlen, tag,
              topic, pubdate, crawldate, publisher, title, description)
              values ('%s', %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s')""" % \
              (url, textlen, tag, topic,str(pubdate), str(crawldate),\
                re.escape(publisher), title, desc)
        try:
            urlid = self.db.insert(sql)
            return urlid
        except Exception, e :
            if self.debug:
               print >> sys.stderr, "ERROR: can't add url metadata.", e
            return None     
        
    def add_freq_index(self, words, table, field, urlid):
        """
        Save the bag of words into database
        """
        for word in words:
            wordid = self.db.getentryid('wordlist', 'word', word)
            self.__update_docfreq(wordid, field)
            try:
                self.db.execute("insert into %s (urlid, wordid, freq) \
                    values (%d, %d, %d)" % (table, urlid, wordid, words[word]))
            except Exception :
                print "\tAdd index error:", table, urlid, wordid, words[word]

    def __update_docfreq(self, wordid, field, value = 1):
        """
        Update word's document frequency by value. It's used to measure
        inverse doc-freq (IDF)
        @param wordid: word's rowid in table 'wordlist'
        @type wordid: C{int}
        """
        sql = """
                update wordlist
                set %s = %s + %d
                where rowid = %d""" % (field, field, value, wordid)
        try:
            self.db.execute(sql)
        except Exception :
            print "\tUpdate docfreq error:", field, wordid


    def save(self, urlid, url, pubdate, title, desc, text, html=None):
        """
        Save the extracted content on local machine via Python pickle module.
        """
        urlid = str(urlid)
        try:
            savepickle(paths['ainews.news_data'] + "desc/"+ urlid + '.pkl', desc)
            savepickle(paths['ainews.news_data'] + "text/"+ urlid +'.pkl', text)
            #if html!=None: savefile(paths['ainews.news_data'] + "html/"+ urlid +'.html', html)
            meta = (urlid, url, title, pubdate)
            savepickle(paths['ainews.news_data'] + "meta/"+urlid+'.pkl', meta)
        except Exception:
            pass

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL,'en_US.UTF-8')
    # Add local python library path into PYTHONPATH
    sys.path.append('/home/glick/lib/python')
    
    file = "output/submit_news.xml"
    sn = AINewsSubmitNews()
    sn.process(file)
