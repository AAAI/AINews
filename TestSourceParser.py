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
from AINewsSummarizer import AINewsSummarizer
class TestSourceParser():

    def __init__(self):
        self.today = date.today()
        #period = int(config['ainews.period'])
        period = 14
        self.begindate = self.today - timedelta(days = period)
        self.debug = config['ainews.debug']
        
        self.db = AINewsDB()
        self.textprocessor = AINewsTextProcessor()
        self.parser = AINewsParser()
        self.summarizer = AINewsSummarizer()
        
    def test(self):
        """
        Crawl the news by source lists (Search page or RSS).
        """
        rows = loadcsv(paths['ainews.ainews_root']+config['crawler.sources'])
        for row in rows:
            print "Source:", row
            if len(row) < 5: continue
            sourcepage_url = row[0]
            publisher = row[1]
            tag       = row[2]
            type      = row[3]
            if row[4] != "On" and row[4]!="on": continue
            parser = ParserFactory(publisher, type)
            if parser == None: continue
            
            if self.debug: print "Processing: ", publisher, type, tag
            parser.parse_sourcepage(sourcepage_url)
            parser.parse_storypage()
            for candidate in parser.candidates:
                if len(candidate) < 5: 
                    print candidate
                else:
                    print candidate[:3]
                    print "\t\tDESC: ", candidate[3]
                    print "\t\tTEXT: ", candidate[4],'\n\n'
                

t = TestSourceParser()
t.test()
