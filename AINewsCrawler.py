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
from datetime import date, timedelta

from AINewsConfig import config, paths, \
     whitelist_bigrams, whitelist_unigrams, whitelist_trigrams
from AINewsTools import savefile, loadcsv, strip_html, savepickle, loadfile
from AINewsParser import AINewsParser
from AINewsSourceParser import *
from AINewsTextProcessor import AINewsTextProcessor
from AINewsDB import AINewsDB
from AINewsCentroidClassifier import AINewsCentroidClassifier
from AINewsRelatedClassifier import AINewsRelatedClassifier

class AINewsCrawler:
    """ 
    Crawl and parse news from major news websites and stores them into database.
    Read the sources list of major news websites. For each website, it is
    either a search result page or a RSS/Atom Feed. After parsing the
    result page or RSS feed, a bunch of latest news pages need to be
    parsed and retrieved. Each news is analyzed with publishing date to
    ensure it is updated news (default 7 days).
    The parsing work is done by AINewsParser and AINewsSourceParser.
    AINewsParser is a base class for general webpage parse.
    AINewsSourceParser is inheritance class for specific website's parse
    AINewsTextProcess is for word extraction, morphy, and count term freq.
    AINewsCentroidClassifier is used to classify the 19 AI Topics categories.
    AINewsSim is used to remove news reporting the same event.
    AINewsDB is a wrapper for MySQL database to store crawled informaiton.
    """
    def __init__(self):
        self.today = date.today()
        self.debug = config['ainews.debug']
        period = int(config['ainews.period'])
        self.begindate = self.today - timedelta(days = period)
        
        self.db = AINewsDB()
        self.textprocessor = AINewsTextProcessor()
        self.parser = AINewsParser()
        
        self.sourcetype = 'database'   # type is either 'database or file'
        
        # classifier topic
        model_dir = "category/centroid/"
        self.classifier = AINewsCentroidClassifier()
        self.classifier.init_predict(model_dir)
        
        self.related_classifier = AINewsRelatedClassifier()
        
    
    def get_newssources(self):
        """
        Get the news source list either from database or from csv file.
        """
        sources = []
        if self.sourcetype == 'database':
            sql = "select url, parser,description from sources where status = 1"
            rows = self.db.selectall(sql)
            for row in rows:
                items = row[1].split('::')
                sources.append((row[0], items[0], items[1], row[2]))
        else:
            rows = loadcsv(paths['ainews.ainews_root']+config['crawler.sources'])
            for row in rows:
                if len(row) < 5: continue
                if row[4].lower() != "on" : continue
                sourcepage_url = row[0]
                publisher = row[1]
                tag       = row[2]
                type      = row[3]
                sources.append((sourcepage_url, publisher, type, tag))
        return sources
        
    def crawl(self):
        """
        Crawl the news by source lists (Search page or RSS).
        """
        rows = self.get_newssources()
        for row in rows:
            sourcepage_url = row[0]
            publisher = row[1]
            type      = row[2]
            tag       = row[3]
            parser = ParserFactory(publisher, type)
            if parser == None: continue
            if self.debug: print "Crawling from %s by %s:" % (publisher, tag)
            try:
                parser.parse_sourcepage(sourcepage_url)
                parser.parse_storypage()
            except (KeyboardInterrupt):
                if self.debug: print "Quitting early due to keyboard interrupt."
                sys.exit()
            except:
                if self.debug: print "Parser for %s failed." % (publisher)
                continue;
            for candidate in parser.candidates:
                if len(candidate) != 5: continue
                url         = candidate[0]
                title       = re.sub(r'\s+', ' ', candidate[1])
                pub_date    = candidate[2]
                desc        = re.sub(r'\s+', ' ', candidate[3])
                text        = candidate[4]
                if not self.contain_whiteterm(text): continue
                if isinstance(desc, types.StringType):
                    desc = unicode(desc, errors = 'ignore')
                if isinstance(title, types.StringType):
                    title = unicode(title, errors = 'ignore')
                
                wordfreq=self.textprocessor.simpletextprocess(text)
                #topic = self.topic.find_topic(wordfreq)
                topic = ""
                urlid = self.add_urlmeta(url, len(wordfreq), tag, \
                        topic,pub_date, self.today, publisher, title, desc)
                if urlid == None: continue
                self.add_freq_index(wordfreq, 'textwordurl', 'dftext', urlid)
                
                
                # Update 19 categories
                # And RelatedClassifier checks if the news is related or not
                topic = self.classifier.predict(urlid)  # 19 category
                # Related or Notrelated?
                doc_data = self.classifier.get_tfidf(urlid)
                isrelated = self.related_classifier.predict(doc_data)
                if isrelated < 0:
                    topic = "NotRelated"
                # Update the topic in the database
                sql = "update urllist set topic = '%s' where rowid = %d" \
                        % (topic, urlid)
                self.db.execute(sql)
                    
                
                # Save to file
                self.save(urlid, url, str(pub_date), title, desc, text)
                if self.debug:
                    try:
                        print """*{ID:%d} %s (%s - %s)\n\t%s\n\t%s\n\n""" % \
                            (urlid, title, str(pub_date), topic, url, desc )
                    except UnicodeError:
                        pass
                
               
    def crawl_url(self, url):
        """
        Directly crawl news by the url given.
        @param url: Target url news to be crawled.
        @type url: C{string}
        """
        # Retrieve the webpage of the URL link
        res = self.parser.parse_url(url)
        if not res or self.parser.url == None \
            or self.db.isindexed(self.parser.url): return False
            
        
        # Skip if the URL host is listed in blacklist
        elems = self.parser.url.split("/")
        host = elems[2]
        #if host in blacklist_hosts: return False
        
        # Extract text content from the HTML 
        # The return value checks if beautiful soup fail to parse the
        # extracted HTML code from the web page.
        success = self.parser.extract_content(extractdate = True)
        if not success or len(self.parser.text) == 0: return False
        
        if not self.contain_whiteterm(self.parser.text): return False
        
        wordfreq=self.textprocessor.simpletextprocess(self.parser.text)
        #topic = self.topic.find_topic(wordfreq)
        topic = ""
        pub_date = self.parser.pubdate
        desc = self.parser.description
        if isinstance(desc, types.StringType):
            desc = unicode(desc, errors = 'ignore')
        tag = ""
        publisher = host
        title = (self.parser.title).strip()
        urlid = self.add_urlmeta(self.parser.url, len(wordfreq), \
                 tag, topic, pub_date, self.today,  publisher, title, desc)
        # Skip if metadata insertion is failed
        if urlid == None: return False
        
        # Bulid index into database
        self.add_freq_index(wordfreq, 'textwordurl', 'dftext', urlid)
        
        
        # Update 19 categories
        topic = self.classifier.predict(urlid)
        doc_data = self.classifier.get_tfidf(urlid)
        isrelated = self.related_classifier.predict(doc_data)
        if isrelated < 0:
            topic = "NotRelated"
        sql = "update urllist set topic = '%s' where rowid = %d" \
                % (topic, urlid)
        self.db.execute(sql)
        
        # Save to file
        self.save(urlid, self.parser.url, str(pub_date),\
                        title, desc, self.parser.text)
        
        
        if self.debug:
            s = """*{ID:%d} %s (%s - %s)\n\t%s""" % \
                 (urlid, title, str(pub_date), topic, \
                                 self.parser.url )
            print s       
                     
        return True
                
    def crawl_urlfile(self, filename):
        """
        Given a file name, crawl the urls listed in the file.
        @param filename: the file with url list
        @type filename: C{string}
        """
        lines = loadfile(filename)
        for url in lines:
            self.crawl_url(url)        

        
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
            #if self.debug:
            #   print >> sys.stderr, "ERROR: can't add url metadata.", e
            return None     
        
    def add_freq_index(self, words, table, field, urlid):
        """
        Save the bag of words into database
        """
        for word in words.keys():
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
                
           
    def contain_whiteterm(self, text):
        """
        Parse the text for unigrams, bigrams and trigrams. It has to contain
        at least one term from one of the Ngrams to be consider candidate.
        Otherwise, the news is discarded.
        @param text: main text of the news story
        @type text: C{string}
        """
        words = self.textprocessor.unigrams(text)
        if self.__is_intersect(whitelist_unigrams, words):return True
        
        bigrams = self.textprocessor.bigrams(words)
        bis = [' '.join(bi) for bi in bigrams]
        if self.__is_intersect(whitelist_bigrams, bis): return True
        
        trigrams = self.textprocessor.trigrams(words)
        tris = [' '.join(tri) for tri in trigrams]
        if self.__is_intersect(whitelist_trigrams, tris): return True
        
        return False
        
    def __is_intersect(self, whitelist, words):
        """
        Check whether words is listed in the whitelist.
        """
        for word in words:
            if word in whitelist:
                return True
        return False
    
    def save(self, urlid, url, pubdate, title, desc, text, html=None):
        """
        Save the extracted content on local machine via Python pickle module.
        """
        urlid = str(urlid)
        try:
            savepickle("news/desc/"+ urlid + '.pkl', desc)
            savepickle("news/text/"+ urlid +'.pkl', text)
            #if html!=None: savefile("news/html/"+ urlid +'.html', html)
            meta = (urlid, url, title, pubdate)
            savepickle("news/meta/"+urlid+'.pkl', meta)
        except Exception:
            pass
        
    def get_urlinfo(self, id):
        '''
        Retrieve the metadata info via urlid
        @param id: urlid 
        @type id: C{int}
        '''
        row = self.db.selectone(
                """select url, pubdate, title, publisher
                from urllist where rowid = %d""" % id)
        return row
        
