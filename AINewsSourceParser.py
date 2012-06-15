# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

"""
AINewsSourceParser includes a set of parsers inherit from the the AINewsParser.
Each of the parser is desgined specifically for one source/publisher website.
It might be crawling the search page or RSS/Atom feeds and get a list of
candiate news stories. Then it crawls all the news stories down and filter
unrelated and store them into database.
"""

import re
import time
import sys
import feedparser
from datetime import date, datetime, timedelta
from BeautifulSoup import BeautifulSoup, Comment, BeautifulStoneSoup, \
                NavigableString, Declaration, ProcessingInstruction

from AINewsConfig import config, dateformat_regexps
from AINewsParser import AINewsParser
from AINewsTools import strip_html, loadfile2

def ParserFactory(publisher, type):
    """
    A factory method to return a specific parser for the specific news source.
    @param publisher: the source/publisher name
    @type publisher: C{string}
    @param type: either 'search' or 'rss'
    @type type: C{string}
    """
    if publisher == "UserSubmitted": 
        parser = UserSubmittedParser()
    elif publisher == "Wall Street Journal" and type == 'search':
        parser = WSJParser()
    elif publisher == "Forbes" and type == 'search':
        parser = ForbesParser()
    elif publisher == "BBC" and type == 'search':
        parser = BBCParser()
    elif publisher == "CNet" and type == 'search':
        parser = CNetParser()
    elif publisher == "Technology Review" and type == 'search':
        parser = TechnologyReviewParser()
    elif publisher == "Scientific American" and type == 'search':
        parser = ScientificAmericanParser()
    elif publisher == "Discovery" and type == 'search':
        parser = DiscoveryParser()
    elif publisher == "Guardian" and type == 'search':
        parser = GuardianParser()
    elif publisher == "TheTimes" and type == 'search':
        parser = TheTimesParser()
    elif publisher == "ScientificAmerican" and type == 'search':
        parser = ScientificAmericanParser()
    elif publisher == "NPR" and type == 'search':
        parser = NPRParser()
    elif publisher == "Independent" and type == 'search':
        parser = IndependentParser()
    elif publisher == "MSNBC" and type == 'search':
        parser = MSNBCParser()
    elif publisher == "Nature" and type == 'search':
        parser = NatureParser()
    elif publisher == "Times" and type == 'search':
        parser = TimesParser()
    elif publisher == "PCWorld" and type == 'search':
        parser = PCWorldParser()
    elif publisher == "NY Times" and type == 'rss':
        parser = NYTRSSParser()
    elif publisher == "Wired" and type == 'rss':
        parser = WiredRSSParser()
    elif publisher == "Popular Science" and type == 'rss':
        parser = PopularScienceRSSParser()
    elif publisher == "CNN" and type == 'rss':
        parser = CNNRSSParser()
    elif publisher == "MITNews" and type == 'rss':
        parser = MITNewsRSSParser()
    elif publisher == "Wash Post" and type == 'rss':
        parser = WashPostRSSParser()
    elif publisher == "GoogleNews" and type == 'rss':
        parser = GoogleNewsRSSParser()
    elif publisher == "NewScientist" and type == 'rss':    
        parser = NewScientistRSSParser()
    elif publisher == "ZDNet" and type == 'rss':    
        parser = ZDNetRSSParser()
    elif publisher == "Kurzweilai" and type == 'rss':
        parser = KurzweilaiRSSParser()
    elif publisher == "USAToday" and type == 'rss':
        parser = USATodayRSSParser()
    elif publisher == "Engadget" and type == 'rss':
        parser = EngadgetRSSParser()
    elif publisher == "LATimes" and type == 'rss':
        parser = LATimesRSSParser()
    elif publisher == "RobotNet" and type == 'rss':
        parser = RobotNetRSSParser()
    elif publisher == "ScienceDaily" and type == 'rss':
        parser = ScienceDailyRSSParser()
    elif publisher == "IEEE Spectrum" and type == 'rss':
        parser = IEEESpectrumRSSParser()
    elif publisher == "Curata" and type == 'rss':
        parser = CurataRSSParser()
    else:
        parser = None
    return parser

class UserSubmittedParser(AINewsParser):
    """
    Parser for user-submitted news.
    """
    def parse_sourcepage(self, url):
        xmlcontent = loadfile2(url)
        xmlcontent = unicode(xmlcontent, errors = 'ignore')
        try:
            xmlsoup = BeautifulSoup(xmlcontent, \
                        convertEntities = BeautifulStoneSoup.HTML_ENTITIES)
        except Exception, error:
            return False
        
        souplist = xmlsoup.findAll('news')
        for soup in souplist:
            type = self.extract_genenraltext(soup.find('type'))
            if type != "NewArticle":
                return
            
            url = self.extract_genenraltext(soup.find('url'))
            date_str = self.extract_genenraltext(soup.find('date'))
            pub_date = self.extract_date(date_str)

            print "Checking if user-submitted URL exists:", url
            res = self.parse_url(url)
            if not res or self.url == None:
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            title = self.soup.find('title')
            if title != None:
                title = (title.string).encode('utf-8')
                title = re.sub(r'\s+', ' ', title)
            else:
                print "No <title> in", url
                continue
            self.candidates.append([url, title, pub_date])

    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url):
                continue
            text = self.justext_extract(self.html)
            if len(text) == 0: continue
            self.candidates[i].append(text)

class WSJParser(AINewsParser):
    """
    Parser for Wall Street Journal.
    e.g. http://topics.wsj.com/subject/a/Artificial-Intelligence/1830
    """
    def parse_sourcepage(self, url):
        """
        Parser for Wall Street Journal's search page.
        @param url: search page's url
        @type url: C{string}
        """
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        self.soup = self.soup.find('ul', {'class': "newsItem"})
        
        boxes = self.soup.findAll('div', {'class':'tipTargetBox'})  
        [box.extract() for box in boxes]
        comments = self.soup.findAll('a', {'class':'icon comments'})
        [comment.extract() for comment in comments]
        videos = self.soup.findAll('a', {'class':'icon video'})
        [video.extract() for video in videos]
        pros = self.soup.findAll('a', {'class':'icon pro'})
        [pro.extract() for pro in pros]
        
        newsitems = self.soup.findAll('li')
        for item in newsitems:
            # Extract date
            item_small = item.find('small')
            if item_small == None: continue
            date_str = item.find('small').getText()
            pub_date = self.parse_date(date_str[:-11], "Month DD, YYYY")
            if pub_date < self.begindate: continue
            # Extract URL
            url  = item.find('a',href=True)['href']
            if url[7:12]=='blogs': continue
            # Extract title
            title = ' '.join([t.getText() for t in item.findAll('a')])
            # Extract description
            
            self.candidates.append([url, title, pub_date])
    
    def parse_storypage(self):
        """
        Parse the story webpage extracting the latest news. The story text is
        extracted. The story's info are stored in the self.candidates.
        """
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            args = ("div", "id", "article_story_body")
            mysoups = self.soup.findAll(args[0], {args[1] : args[2]})
            text = ""
            for mysoup in mysoups:
                paragraphs = mysoup.findAll('p')
                for paragraph in paragraphs:
                    text += paragraph.getText() + ' '
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
          
class ForbesParser(AINewsParser):
    """
    Parser for Forbes.
    e.g. http://search.forbes.com/search/find?&start=1&tab=searchtabgeneraldark
         &MT=artificial+intelligence&sort=Date
    """
    def parse_sourcepage(self, url):
        """
        Parser for Forbes's search page.
        @param url: search page's url
        @type url: C{string}
        """
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        mysoups = self.soup.findAll('div', {'class': "head"})
        for mysoup in mysoups:
            item = mysoup.find('a',href=True)
            url  = item['href']
            if url[7:12] == 'blogs': continue
            title = item.getText()
            s = re.search('20\d\d\/(0|1)\d\/(0|1|2|3)\d', url)
            if s == None: continue
            date_str = s.group(0)
            t = time.strptime(date_str,"%Y/%m/%d")
            d = date(t[0], t[1], t[2])
            if d > self.today or d < self.begindate: continue
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
           
            descsoup = self.soup.find('meta', {'name': 'description'})
            desc = descsoup['content']
            mysoups = self.soup.findAll("div", {"id" : "storyBody"})
            text = ""
            for mysoup in mysoups:
                cbx = mysoup.find('div',{'id':'controlsbox'})
                if cbx != None: cbx.extract()
                paragraphs = mysoup.findAll('p')
                for paragraph in paragraphs:
                    text += paragraph.getText() + ' '
            text = re.sub(r'&.*?;', ' ', text)
            if len(text) == 0:   continue
            self.candidates[i].append(text)
            
class BBCParser(AINewsParser):
    """
    Parser for BBC News.
    e.g. http://search.bbc.co.uk/search?go=toolbar&tab=ns&q=robots&order=date
         &scope=all
    """
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        
        newssoup = self.soup.find('li', {'class':"DateItem leadDate"})
        date_str = newssoup.find('div',{'class':"newsDateView"}).getText()
        if date_str == "": return
        t = time.strptime(date_str,"%d %B %Y")
        d = date(t[0], t[1], t[2])
        if d > self.today or d < self.begindate: return
        mysoups = newssoup.findAll('li',{'class': "thumbItem lead"})
        for mysoup in mysoups:
            url = mysoup.find('a', href=True)['href']
            item = mysoup.find('a')
            if item == None: continue
            
            #title = item.getText()
            title = self.extract_genenraltext(item)
            """
            desc = mysoup.find('p',{'class': "abstract"}).getText()
            """
            
            self.candidates.append([url, title, d])
            
    #http://www.bbc.co.uk/search/news/artificial_intelligence
    def parse_sourcepage2(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        
        newssoup = self.soup.find('div', {'id': "newsBbc"})
        mysoups = newssoup.findAll('li')
        for mysoup in mysoups:
            date_str = ""
            for s in mysoup.findAll('span'):
                m = re.search('\d\d \w\w\w \d\d', s.getText())
                if m != None:
                    date_str=m.group(0)
                    break
            if date_str == "": continue
            t = time.strptime(date_str,"%d %b %y")
            d = date(t[0], t[1], t[2])
            if d > self.today or d < self.begindate: continue
            
            url = mysoup.find('a', href=True)['href']
            item = mysoup.find('a',{'class':'title'})
            if item == None: continue
            title = item.getText()
            
            """
            desc = self.extract_genenraltext( mysoup.find('p'))
            desc = re.sub(r'\n+', ' ', desc)
            """
            
            self.candidates.append([url, title, d])
         
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            mainsoup = self.soup.find("div", {"id" : "main-content"})
            if mainsoup == None:
                mainsoup = self.soup.find("table", {"class" : "storycontent"})
                if mainsoup == None: continue
            text = ""
            mysoups = mainsoup.findAll('p')
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup) + ' '
            dummy="Please turn on JavaScript. Media requires JavaScript to play."
            if text[:61]== dummy:
                text = text[61:]
            text = re.sub(r'&.*?;', ' ', text)
            if len(text) == 0:   continue
            
            self.candidates[i][0] = self.url
            self.candidates[i].append(text)
            
class CNetParser(AINewsParser):
    """
    Parser for CNet.
    e.g. http://news.cnet.com/1770-5_3-0.html?tag=mncol%3Bsort&query=artificial
         +intelligence&searchtype=news&source=news&rpp=10&sort=updateDate+desc
    """
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        newssoup = self.soup.find('div', {'id': "contentBody"})
        mysoups = newssoup.findAll('div',{'class':'resultInfo'})
        for mysoup in mysoups:
            str = mysoup.find('span',{'class':'resultDetails'}).getText()
            regexp = dateformat_regexps["Month DD, YYYY"][0]
            res = re.search(regexp, str, re.IGNORECASE)
            date_str = res.group(0)
            t = time.strptime(date_str,dateformat_regexps["Month DD, YYYY"][1])
            d = date(t[0], t[1], t[2])
            if d > self.today or d < self.begindate: continue
            
            url = mysoup.find('a', href=True)['href']
            if url[:4] != 'http':
                url = "http://news.cnet.com" + url
            title = mysoup.find('a',{'class':'resultName'}).getText()
            if len(title)>=5 and title[-5:] == 'blog)': continue
            if len(title)>=9 and title[-9:] == '(podcast)': continue
            if title[:18] == "This week in Crave":continue
            desc = mysoup.find('div',{'class':'resultSummary'}).getText()
            self.candidates.append([url, title, d, desc])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"id" : "contentBody"})
            if mainsoup == None:
                mainsoup = self.soup.find("div", {"class" : "txtWrap"})
                if mainsoup == None:continue
            posts = mainsoup.findAll('div', {'class':'postTalkback'})
            [post.extract() for post in posts]
            
            text = ""
            mysoups = mainsoup.findAll('p')
            for mysoup in mysoups:
                text += mysoup.getText() + ' '
            text = re.sub(r'&.*?;', ' ', text)
           
            if len(text) == 0:   continue
            self.candidates[i][0] = self.url
            self.candidates[i].append(text)
            
class TechnologyReviewParser(AINewsParser):
    """
    Parser for Technology Review.
    e.g. http://www.technologyreview.com/search.aspx?s=artificial%20intelligence
         &limit=computing&sort=date
    """
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        mysoups = self.soup.findAll('div',{'class':'SearchResult'})
        for mysoup in mysoups:
            res = mysoup.find('dd',{'class':'Author'}).getText()
            date_str = res.split('|')[1].strip()
            t = time.strptime(date_str,"%m/%d/%Y")
            d = date(t[0], t[1], t[2])
            if d > self.today or d < self.begindate: continue
            
            res = mysoup.find('dt',{'class':'Headline'})
            title = self.extract_genenraltext(res)
            url = res.find('a')['href']
            res = mysoup.find('dd',{'class':'SearchDek'})
            if res== None: continue
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            text = ""
            mainsoup = self.soup.find("div", {"id" : "articlebody"})
            if mainsoup != None: 
                mysoups = mainsoup.findAll('p')
                for mysoup in mysoups:
                    text += mysoup.getText().strip() + ' '
            else:
                mainsoups = self.soup.findAll("div", {"class" : "blogcontent"})
                if mainsoups == None: continue
                for mainsoup in mainsoups:
                    mysoups = mainsoup.findAll('p')
                    for mysoup in mysoups:
                        text += self.extract_genenraltext(mysoup) + ' '
            text = re.sub(r'\s+', ' ', text)
            
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
            
class ScientificAmericanParser(AINewsParser):
    """
    Parser for Scientific American.
    e.g. http://www.scientificamerican.com/search/index.cfm?i=1&q=artificial+
         intelligence&sort=publish_date&submit=submit&submit.x=0&submit.y=0&u1=q
    """
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        newssoup = self.soup.find('div', {'id': "searchpage"})
        newssoup.find('div', {'id':'search_advertise'}).extract()
        items = newssoup.findAll('h5')
        dates = newssoup.findAll('span', {'class': "searchdates"})
        for i, item in enumerate(items):
            title = item.getText()
            title = re.sub(r'&.*?;', ' ', title)
            url   = item.find('a')['href']
            if re.search('podcast|blog', url) != None: continue
            if i >= len(dates): break
            date_str = ' '.join(dates[i].getText().split(' ')[:3])
            d = self.parse_date(date_str, "Month DD, YYYY")
            if d > self.today or d < self.begindate: continue
            self.candidates.append([url, title, d])
        
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            mainsoup = self.soup.find("div", {"id" : "article"})
            if mainsoup == None: continue
            text = ""
            mysoups = mainsoup.findAll('p')
            for mysoup in mysoups:
                text += mysoup.getText().strip() + ' '
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
            
class DiscoveryParser(AINewsParser):
    """
    Parser for Discovery News.
    e.g. http://news.discovery.com/robots/
    """
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        mysoups = self.soup.findAll('dl',{'class':'asset-items clear clearfix'})
        for mysoup in mysoups:
            source = mysoup.find('p',{"class":"source"}).getText()
            m = re.search(dateformat_regexps['Mon DD, YYYY'][0], source)
            if m != None:
                date_str = m.group(0)
                d = self.parse_date(date_str,'Mon DD, YYYY')
                if d > self.today or d < self.begindate: continue
            else:
                d = self.today
            
            item = mysoup.find('h2',{"class":"title"})
            title = item.getText()
            if title[-7:] == '[VIDEO]': continue
            url = item.find('a')['href']
            
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"id" : "article-body"})
            if mainsoup == None: continue
            text = ""
            mysoups = mainsoup.findAll('p')
            for mysoup in mysoups:
                text += mysoup.getText() + ' '
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
            
class GuardianParser(AINewsParser):
    """
    Parser for guardian.co.uk News.
    e.g. http://browse.guardian.co.uk/search?search=%22artificial+intelligence \
        %22&sitesearch-radio=guardian&go-guardian=Search
    """
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        self.soup = self.soup.find('div',{'class':'most-recent-results'})
        mysoups = self.soup.findAll('li',{'class':'l1'})
        for mysoup in mysoups:
            source = mysoup.find('p',{'class':'publication'}).getText()
            m = re.search(dateformat_regexps['DD Mon YYYY'][0], source)
            if m != None:
                date_str = m.group(0)
                d = self.parse_date(date_str,'DD Mon YYYY')
                if d > self.today or d < self.begindate: continue
            else:
                d = self.today
                
            item = mysoup.find('h3',{'class':'t2'})
            title = item.getText()
            url = item.find('a')['href']
            self.candidates.append([url, title, d])
        
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            mainsoup = self.soup.find("div", {"id" : "article-wrapper"})
            if mainsoup == None: continue
            text = ""
            mysoups = mainsoup.findAll('p')
            for mysoup in mysoups:
                #text += mysoup.getText() + ' '
                text += self.extract_genenraltext(mysoup)+' '
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)

class TheTimesParser(AINewsParser):
    """
    Parser for The Times.
    Default is turned off since all the news in TheTimes require
    registration and pay fee.
    e.g. http://www.thetimes.co.uk/tto/public/sitesearch.do?querystring=
         artifical+intelligence&sectionId=342&p=tto&pf=all
    """
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        
        mainmysoup = self.soup.find('div', {'class': "content-box-margin"})
        mysoups = mainmysoup.findAll('div',{'class': 'search-result'})
        for mysoup in mysoups:
            item = mysoup.find('a',href=True)
            url  = item['href']
            title = item.getText()
            info = mysoup.find('div', {'class':'search-result-info'})
            s = ""
            s = ' '.join([li.getText() for li in info.findAll('li')])
            m = re.search(dateformat_regexps['DD Month YYYY'][0], s)
            if m != None:
                date_str = m.group(0)
                d = self.parse_date(date_str,'DD Month YYYY')
                if d > self.today or d < self.begindate: continue
            else:
                d = self.today
            
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        pass
        """
        # It is pending because the news require registration and pay.
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
        """
class ScientificAmericanParser(AINewsParser):
    """
    Parser for ScientificAmerican.
    e.g. http://www.scientificamerican.com/topic.cfm?id=artificial-intelligence
    Date: Dec.21st, 2010
    """
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        
        mainmysoup = self.soup.find('div', {'id': "mainCol"})
        mysoups = mainmysoup.findAll('li',{'class': 'hasThumb message_box'})
        for mysoup in mysoups:
            titlesoup = mysoup.find('h3')
            item = titlesoup.find('a',href=True)
            url  = item['href']
            title = self.extract_genenraltext(item)
            info = mysoup.find('span', {'class':'datestamp'})
            s = self.extract_genenraltext(info)
            m = re.search(dateformat_regexps['Mon DD, YYYY'][0], s)
            if m != None:
                date_str = m.group(0)
                d = self.parse_date(date_str,'Mon DD, YYYY')
                if d > self.today or d < self.begindate: continue
            else:
                d = self.today
            
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            mainsoup = self.soup.find("div", {"id" : "articleContent"})
            if mainsoup == None: continue
            text = ""
            imgs = mainsoup.findAll("p",{"class":"in-article-image"})
            [img.extract() for img in imgs]
            spans = mainsoup.findAll("span")
            [span.extract() for span in spans]
            text = self.extract_genenraltext(mainsoup)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
 
class NPRParser(AINewsParser):
    """
    Parser for NPR.
    e.g. http://www.npr.org/templates/search/index.php?searchinput=artificial+intelligence&tabId=all&sort=date
    Date: Dec.22nd, 2010
    """
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        
        mainmysoup = self.soup.find('div', {'id': "searchresults"})
        mainmysoup = mainmysoup.find('ol',{'class':'result'})
        mysoups = mainmysoup.findAll('li',{'class': 'buildOut'})
        for mysoup in mysoups:
            titlesoup = mysoup.find('h3')
            item = titlesoup.find('a',href=True)
            if item == None: continue
            url  = item['href']
            if url.find("movie")!=-1: continue
            title = self.extract_genenraltext(item)
            info = mysoup.find('span', {'class':'date'})
            s = self.extract_genenraltext(info)
            m = re.search(dateformat_regexps['Month DD, YYYY'][0], s)
            if m != None:
                date_str = m.group(0)
                d = self.parse_date(date_str,'Month DD, YYYY')
                if d > self.today or d < self.begindate: continue
            else:
                d = self.today
            
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            titlesoup = self.soup.find('title')
            if titlesoup!=None:
                title = self.extract_genenraltext(titlesoup)
                self.candidates[i][1] = title
            mainsoup = self.soup.find("div", {"id" : "storytext"})
            if mainsoup == None: continue
            
            comments = mainsoup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]
            #wraps = mainsoup.findAll("div",{"class":"captionwrap"})
            #[wrap.extract() for wrap in wraps]
            self.remove_tag(mainsoup, "div","class","captionwrap")
            self.remove_tag(mainsoup, "div","class","dateblock")
            self.remove_tag(mainsoup, "div","class","bucket")
            self.remove_tag(mainsoup, "div","id","res132205459")
            self.remove_tag(mainsoup, "div","class","container con1col btmbar")
            self.remove_tag(mainsoup, "div","class","captionwrap enlarge")
            
            text = self.extract_genenraltext(mainsoup)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)

class IndependentParser(AINewsParser):
    '''
    Parser for Independent UK
    e.g. http://search.independent.co.uk/topic/artificial-intelligence
    Date: Dec.23rd, 2010
    '''
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        mainmysoup = self.soup.find('ul', {'class': "ukn-results ukn-col-first"})
        mysoups = mainmysoup.findAll('li')
        for mysoup in mysoups:
            titlesoup = mysoup.find('h2')
            item = titlesoup.find('a',href=True)
            if item == None: continue
            url  = item['href']
            title = item['title']
            info = mysoup.find('span', {'class':'ukn-result-meta-date'})
            s = self.extract_genenraltext(info)
            m = re.search(dateformat_regexps['DD Month YYYY'][0], s)
            if m != None:
                date_str = m.group(0)
                d = self.parse_date(date_str,'DD Month YYYY')
                if d > self.today or d < self.begindate: continue
            else:
                d = self.today
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"id" : "article"})
            if mainsoup == None: continue
            comments = mainsoup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]
            mainsoup.prettify()
            self.remove_tag(mainsoup, 'script')
            self.remove_tag(mainsoup, 'p','class','title')
            self.remove_tag(mainsoup, 'p','class','author')
            self.remove_tag(mainsoup, 'p','class','info')
            
            mysoups = mainsoup.findAll('p')
            text = ""
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup) + ' '
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
            
class MSNBCParser(AINewsParser):
    '''
    Parser for MSNBC
    e.g. http://www.msnbc.msn.com/id/33732970/
    Date: Dec.23rd, 2010
    '''
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        mainmysoup = self.soup.find('div', {'id': "cover"})
        mysoups = mainmysoup.findAll('div',{'class':'text'})
        for mysoup in mysoups:
            item = mysoup.find('a',href=True)
            if item == None: continue
            url  = item['href']
            if url[:10]=='javascript': continue
            title = self.extract_genenraltext(item)
            
            d = self.today
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            datesoup = self.soup.find("div", {"class" : "txt timestamp"})
            if datesoup!=None:
                date_str = datesoup['content'][:10]
                d = self.parse_date(date_str,'YYYY-MM-DD')
                self.candidates[i][2] = d
                if d > self.today or d < self.begindate: continue
            
            mainsoup = self.soup.find("div", {"class" : "page i1 txt"})
            if mainsoup == None: continue
            
            self.remove_tag(mainsoup, 'span','class','copyright')
            self.remove_tag(mainsoup, 'ul','class','extshare hlist')
            
            mysoups = mainsoup.findAll('p')
            text = ""
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup) + ' '
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)

class NatureParser(AINewsParser):
    '''
    Parser for Nature News
    e.g. http://www.nature.com/search/executeSearch?exclude-collections=
    journals_palgrave%2Clab_animal&sp-q-1=&include-collections=journals_nature%2Ccrawled_content&
    sp-a=sp1001702d&sp-x-1=ujournal&sp-sfvl-field=subject|ujournal&sp-q=robot&sp-p=all&
    sp-p-1=phrase&sp-s=date_descending&sp-c=5
    '''
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        mainmysoup = self.soup.find('ol', {'class': "results-list"})
        mysoups = mainmysoup.findAll('li')
        for mysoup in mysoups:
            titlesoup = mysoup.find('h2')
            item = titlesoup.find('a',href=True)
            # an "access" span element indicates "free"
            access = titlesoup.find('span', {'class': 'access'})
            if item == None or access == None: continue
            url  = item['href']
            title = self.extract_genenraltext(item).strip()
            if title == 'News in brief': continue
            date_str = mysoup.find('span', {'class': 'date'}).content
            d = self.extract_date(date_str)
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            mainsoup = self.soup.find("div", {"class" : "content"})
            if mainsoup == None: continue
            self.remove_tag(mainsoup, 'div', 'class', 'article-tools')
            mysoups = mainsoup.findAll('p')
            text = ""
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup) + ' '
                
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)


class TimesParser(AINewsParser):
    '''
    Parser for Times
    e.g. http://search.time.com/results.html?cmd=tags&D=robot&
    sid=12D1588BC3C6&Ntt=robot&internalid=endeca_dimension
    &Ns=p_date_range|1&p=0&N=34&Nty=1&srchCat=Full+Archive
    Date: Dec.23rd, 2010
    '''
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        mainmysoup = self.soup.find('div', {'class': "resultsCol"})
        if mainmysoup == None: return
        mysoups = mainmysoup.findAll('div', {'class':'tout'})
        for mysoup in mysoups:
            titlesoup = mysoup.find('h3')
            item = titlesoup.find('a',href=True)
            if item == None: continue
            url  = item['href']
            title = self.extract_genenraltext(titlesoup)
            info = mysoup.find('span', {'class':'date'})
            s = self.extract_genenraltext(info)
            m = re.search(dateformat_regexps['Mon DD, YYYY'][0], s)
            if m != None:
                date_str = m.group(0)
                d = self.parse_date(date_str,'Mon DD, YYYY')
                if d > self.today or d < self.begindate: continue
            else:
                d = self.today
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            if candidate[0].find('newsfeed')!=-1:
                # is newsfeed
                mainsoup = self.soup.find("div", {"id" : "content"})
                if mainsoup == None: continue
                self.remove_tag(mainsoup, 'p','id','description')
                self.remove_tag(mainsoup, 'p','id','caption')
            else:
                # not newsfeed
                mainsoup = self.soup.find("div", {"class" : "artTxt"})
                if mainsoup == None: continue
            comments = mainsoup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]
            mysoups = mainsoup.findAll('p')
            text = ""
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup) + ' '
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)

class PCWorldParser(AINewsParser):
    '''
    Parse for PC World Magzine
    e.g. http://www.pcworld.com/search2/news?qt=%22artificial+intelligence%22
    '''
    def parse_sourcepage(self, url):
        self.parse_url(url)
        try:
            self.soup = BeautifulSoup(self.html)
        except Exception, error:
            if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
        mainmysoup = self.soup
        mysoups = mainmysoup.findAll('li', {'class':'clearfix'})
        for mysoup in mysoups:
            item = mysoup.find('a',href=True)
            if item == None: continue
            url  = item['href']
            if url[0] == '/':
                url = 'http://www.pcworld.com'+url
            res = self.parse_url(url)
            if not res: continue
            try:
                soup = BeautifulSoup(self.html)
                date_container = soup.find("p", {"class" : "byline"})
                date_str = date_container.contents[0]
                if date_str == None: d = self.today
                else: d = self.extract_date(date_str)
                title = soup.find("h1").string
            except: continue
            if d == None: d = self.today
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            flag = False
            date_str = ''
            metas = self.soup.findAll('meta')
            for meta in metas:
                if meta.has_key('name')  \
                    and re.search('date|create|time', meta['name'], \
                                  re.IGNORECASE)!= None:
                    date_str = meta['content'][:10]
                    flag = True
                    break
            if flag:
                
                d = self.parse_date(date_str,'YYYY-MM-DD')
                self.candidates[i][2] = d
                if d > self.today or d < self.begindate: continue
            
            mainsoup = self.soup.find("div", {"class" : "articleBodyContent"})
            if mainsoup == None: continue
            self.remove_tag(mainsoup, 'object')
            self.remove_tag(mainsoup, 'em')
            mysoups = mainsoup.findAll('p')
            text = ""
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup) + ' '
                
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
                    



class NYTRSSParser(AINewsParser):
    """
    RSS parser for New York Times.
    e.g. http://topics.nytimes.com/top/reference/timestopics/subjects/a/
         artificial_intelligence/index.html?rss=1
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                           entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            url = entry.link[:-23]
            title = entry.title
            desc = re.sub(r'</?(a|img).*?>', ' ', entry.description).strip()
            
            self.candidates.append([url, title, d, desc])
            
    
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            mysoups = self.soup.findAll("div", {"class" : "articleBody"})
            text = ""
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup) + ' '
            text = re.sub(r'&.*?;', ' ', text)
            if len(text) == 0: continue
            m = re.search(r'\?', self.url)
            #self.candidates[i][0] = self.url[:m.start()]
            self.candidates[i].append(text)
            
            
            
class PopularScienceRSSParser(AINewsParser):
    """
    RSS parser for Popular Science.
    e.g. http://www.popsci.com/full-feed/technology
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                           entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            """
            # pop sci has the longest description text
            try:
                descsoup = BeautifulSoup(entry.description)
            except Exception, error:
                if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
                return False
            [mysoup.extract() for mysoup in descsoup.findAll('a')]
            comments = descsoup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]
            ci = descsoup.find('div',{'class':'center-image'})
            if ci!=None: ci.extract()
            desc = descsoup.getText()
            if desc[-2:] == '[]': desc = desc[:-2]
            if desc[-5:] == '[via]': desc = desc[:-5]
            """
            
            self.candidates.append([entry.link, entry.title, d])
     
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None \
                or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
       
            comments = self.soup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]
            scripts = self.soup.findAll('script')
            [script.extract() for script in scripts]
            blocks = self.soup.findAll('div',{'class':"block block-block clear-block"})
            [block.extract() for block in blocks]
            submits = self.soup.findAll('div',{'class':'submitted'})
            [submit.extract() for submit in submits]
            submits = self.soup.findAll('div',{'class':'relatedinfo related-right'})
            [submit.extract() for submit in submits]
            objects = self.soup.findAll('object')
            [object.extract() for object in objects]
            mainsoups = self.soup.findAll("div", {"class" : "content"})
            if mainsoups == None: continue
            text = ""
            for mainsoup in mainsoups:
                mysoups = mainsoup.findAll('p')
                for mysoup in mysoups:
                    text += self.extract_genenraltext(mysoup) + ' '
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
            
class CNNRSSParser(AINewsParser):
    """
    RSS parser for CNN News.
    e.g. http://rss.cnn.com/rss/cnn_tech.rss
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                           entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            
            """
            try:
                descsoup = BeautifulSoup(entry.description)
            except Exception, error:
                if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
                return False
            feedflares = descsoup.findAll('div',{'class':'feedflare'})
            [feedflare.extract() for feedflare in feedflares]
            imgs = descsoup.findAll('img')
            [img.extract() for img in imgs]
            desc = descsoup.getText()
            """
            self.candidates.append([entry.link, entry.title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"id" : "cnnContentContainer"})
            if mainsoup == None: continue
            comments = mainsoup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]
            scripts = mainsoup.findAll('script')
            [script.extract() for script in scripts]
            tools = mainsoup.findAll('div',{"class":"cnn_strybtntools"})
            [tool.extract() for tool in tools]
            tools = mainsoup.findAll('div',{"class":"cnnShareThisItem"})
            [tool.extract() for tool in tools]
            imgs = mainsoup.findAll('img')
            [img.extract() for img in imgs]
            text = ""
            mysoups = mainsoup.findAll('p')
            for mysoup in mysoups:
                text += mysoup.getText() + ' '
            text = re.sub(r'&.*?;', ' ', text)
            m = re.search(r'\?', self.url)
            self.candidates[i][0] = self.url[:m.start()]
            self.candidates[i].append(text)

class MITNewsRSSParser(AINewsParser):
    """
    RSS parser for MIT News.
    e.g. http://web.mit.edu/newsoffice/topic/robotics.feed?type=rss
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                           entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            try:
                descsoup = BeautifulSoup(entry.description)
            except Exception, error:
                if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
                return False
            
            text = self.extract_genenraltext(descsoup)
            
            dsoup = descsoup.find('p')
            if dsoup != None: desc = dsoup.getText()  
            else:
                m = re.search(r'<br />', entry.description)
                desc = strip_html(entry.description[:m.start()])
            
            self.candidates.append([entry.link, entry.title, d, text])
    def parse_storypage(self):
        pass

            

class WiredRSSParser(AINewsParser):
    """
    RSS parser for Wired News.
    e.g.http://www.wired.com/wiredscience/feed/
    """
    def parse_sourcepage(self, rss_url):
        try:
            f = feedparser.parse(rss_url)
        except Exception, error:
            if self.debug: print >> sys.stderr, "feedparser ERROR: %s" % error
            return False            
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                           entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            url = entry.link
            title = entry.title
            self.candidates.append([url, title, d])
    
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
               
            
            mainsoup = self.soup.find("div", {"class" : "entry"})
            if mainsoup == None: continue
            
            [ul.extract() for ul in mainsoup.findAll('ul')]
            [img.extract() for img in mainsoup.findAll('img')]
            [script.extract() for script in mainsoup.findAll('script')]
            text = ""
            mysoups = mainsoup.findAll('p')
            for mysoup in mysoups:
                text +=  self.extract_genenraltext(mysoup) + ' '
            text = re.sub(r'&.*?;', ' ', text)
            m = re.search(r'\?', self.url)
            self.candidates[i].append(text)
            

class WashPostRSSParser(AINewsParser):
    """
    RSS parser for Washington Post.
    e.g. http://www.washingtonpost.com/wp-dyn/rss/technology/index.xml
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                    entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            
            url = entry.link
            title = entry.title
            """
            try:
                descsoup = BeautifulSoup(entry.description)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            desc = descsoup.getText()
            """
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find('div', {'id':'article_body'})
            if mainsoup == None: continue
            text = ""
            mysoups = mainsoup.findAll('p')
            for mysoup in mysoups:
                text +=  self.extract_genenraltext(mysoup) + ' '
            text = re.sub(r'__', '', text)
            text = re.sub(r'&.*?;', '', text)
            m = re.search(r'\?', self.url)
            self.candidates[i].append(text)
            self.candidates[i][0] = self.url
            

class NewScientistRSSParser(AINewsParser):
    """
    RSS parser for NewScientist
    e.g. http://feeds.newscientist.com/tech
    Create Date: Dec. 21th, 2010
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                    entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            
            url = entry.link
            title = entry.title
            
            self.candidates.append([url, title, d])
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
               
            
            mainsoup = self.soup.find("div", {"id" : "maincol"})
            if mainsoup == None: continue
            #mainsoup.find("div", {"id":"sharebtns"}).extract()
            text = ""
            mysoups = mainsoup.findAll('p',{"class":"infuse"})
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup) + ' '
            text = re.sub(r'&.*?;', ' ', text)
            m = re.search(r'\?', self.url)
            self.candidates[i].append(text)
            
class ZDNetRSSParser(AINewsParser):
    """
    RSS parser for ZDNet
    e.g. http://www.zdnet.com/topics/robots?o=1&mode=rss&tag=mantle_skin;content
    Create Date: Dec. 21th, 2010
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                    entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            
            url = entry.link
            title = entry.title
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"class" : "content-1 entry space-1 clear"})
            if mainsoup == None: continue
            scripts = mainsoup.findAll("script")
            [script.extract() for script in scripts]
            videos = mainsoup.findAll('div',{"class":"video-player"})
            [video.extract() for video in videos]
            if mainsoup == None: continue
            #mainsoup.find("div", {"id":"sharebtns"}).extract()
            text = ""
            mysoups = mainsoup.findAll('p')
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup) + ' '
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            m = re.search(r'\?', self.url)
            self.candidates[i].append(text)
    
    
class KurzweilaiRSSParser(AINewsParser):
    """
    RSS parser for Kurzweilai
    e.g. http://www.kurzweilai.net/news/feed
    Create Date: Dec. 21th, 2010
    """
    def parse_sourcepage(self, rss_url):
        try:
            f = feedparser.parse(rss_url)
        except Exception, error:
            print >> sys.stderr, "feedparser error in KurzweilaiRSSParser"
            return
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                    entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            
            try:
                descsoup = BeautifulSoup(entry.description)
            except Exception, error:
                if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
                return False
            
            url = entry.link
            title = entry.title
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"class" : "body"})
            if mainsoup == None: continue
            
            origin = mainsoup.find('p', {'class':'read-original'})
            if origin!=None:
                url = origin.find('a')['href']
                self.candidates[i][0] = url
                origin.extract()
            caption = mainsoup.find('p',{'class':'wp-caption-text'})
            if caption != None: caption.extract()
                
            mysoups = mainsoup.findAll('p')
            text = ''
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup)+' '
            text = re.sub(r'\s+', ' ', text)
            if len(text) < 600: continue
            text = re.sub(r'&.*?;', ' ', text)
            m = re.search(r'\?', self.url)
            self.candidates[i].append(text)
            
class USATodayRSSParser(AINewsParser):
    """
    RSS parser for USAToday
    e.g. http://rssfeeds.usatoday.com/usatoday-TechTopStories
    Create Date: Dec. 22th, 2010
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                    entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            
            url = entry.link
            title = entry.title
            
            self.candidates.append([url, title, d])
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"id" : "yui-main"})
            if mainsoup == None: continue
            tools = mainsoup.find('div',{"class":"pagetools"})
            if tools != None: tools.extract()
            scripts = mainsoup.findAll("script")
            [script.extract() for script in scripts]
            nav = mainsoup.find('div', {'class':'post-navigation'})
            if nav!=None: nav.extract()
            styles = mainsoup.findAll("style")
            [style.extract() for style in styles]
            tags = mainsoup.findAll('div', {'class':'tags'})
            [tag.extract() for tag in tags]
            footer = self.soup.find('div', {'class':'post-navigation footer'})
            if footer!=None: footer.extract()
            comments = self.soup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]
            
            
            mysoups = mainsoup.findAll('p')
            text = ''
            for mysoup in mysoups:
                text += self.extract_genenraltext(mysoup)+' '
            text = re.sub(r'\s+', ' ', text)
            if len(text)< 500: continue
            text = re.sub(r'&.*?;', ' ', text)
            m = re.search(r'\?', self.url)
            self.candidates[i].append(text)

class EngadgetRSSParser(AINewsParser):
    """
    RSS parser for Engadget.
    e.g. http://www.engadget.com/tag/Robot/rss.xml
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                    entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            
            url = entry.link
            title = entry.title
            self.candidates.append([url, title, d])
            
            
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url): continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"class" : "post_body"})
            imgs = mainsoup.findAll("img")
            [img.extract() for img in imgs]
            objects = mainsoup.findAll("object")
            [object.extract() for object in objects]
            comments = self.soup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]

            text = self.extract_genenraltext(mainsoup)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
           
           
class LATimesRSSParser(AINewsParser):
    """
    RSS parser for Los Angles Times.
    e.g. http://feeds.latimes.com/TheTechnologyBlog
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                    entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            
            try:
                descsoup = BeautifulSoup(entry.content[0]['value'])
            except Exception, error:
                if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
                return False
            
            self.remove_tag(descsoup, 'img')
            self.remove_tag(descsoup, 'strong')
            self.remove_tag(descsoup, 'em')
            text = self.extract_genenraltext(descsoup)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            url = entry.link
            title = entry.title
            self.candidates.append([url, title, d, text])
            
    def parse_storypage(self):
        pass
    
    
class RobotNetRSSParser(AINewsParser):
    """
    RSS parser for Robot.net
    e.g. http://robots.net/rss/articles.xml
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                    entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            
            url = entry.link
            title = entry.title
            self.candidates.append([url, title, d])
                
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"id" : "col1"})
            self.remove_tag(mainsoup,'img')
            self.remove_tag(mainsoup,'object')
            self.remove_tag(mainsoup,'h1')
            self.remove_tag(mainsoup,'h2')
            self.remove_tag(mainsoup,'h4')
            comments = self.soup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]

            text = self.extract_genenraltext(mainsoup)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
    
class GoogleNewsRSSParser(AINewsParser):
    """
    RSS parser for Google News.
    e.g. http://news.google.com/news?pz=1&cf=all&ned=us&hl=en&q=artificial
         +intelligence&cf=all&output=rss
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                           entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            if entry.title[-6:] == '(blog)' \
                or entry.title[-15:] == '(press release)': continue

            url = re.sub(r'.*?url=(.*)', r'\1', entry.link)
            
            self.candidates.append([url, entry.title, d])
                
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url):
                continue
            text = self.justext_extract(self.html)
            if len(text) == 0: continue
            self.candidates[i].append(text)

class ScienceDailyRSSParser(AINewsParser):
    """
    RSS parser for ScienceDaily
    e.g. http://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                    entry.published_parsed[1], entry.published_parsed[2])
            if d > self.today or d < self.begindate: continue
            
            url = entry.link
            title = entry.title
            self.candidates.append([url, title, d])
                
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"id" : "story"})
            self.remove_tag(mainsoup,'div','id','seealso')
            self.remove_tag(mainsoup,'span','class','date')
            self.remove_tag(mainsoup,'img')
            self.remove_tag(mainsoup,'object')
            self.remove_tag(mainsoup,'h1')
            self.remove_tag(mainsoup,'h2')
            self.remove_tag(mainsoup,'h4')
            comments = self.soup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]

            text = self.extract_genenraltext(mainsoup)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
  
class IEEESpectrumRSSParser(AINewsParser):
    """
    RSS parser for IEEE Spectrum
    e.g. http://feeds.feedburner.com/IeeeSpectrumAI?format=xml
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            # dates not available, so follow the link to find the date
            url = entry.link
            res = self.parse_url(url)
            if not res:
                continue
            try:
                soup = BeautifulSoup(self.html)
                date_container = soup.find("p", {"class" : "articleBodyTtl"})
                date_str = date_container.contents[1]
                d = self.extract_date(date_str)
            except:
                continue
            if d == None:
                continue
            title = entry.title
            self.candidates.append([url, title, d])
                
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None or self.db.isindexed(self.url):
                continue
            try:
                self.soup = BeautifulSoup(self.html)
            except Exception, error:
                print >> sys.stderr, "SOUP ERROR: %s" % error
                continue
            
            mainsoup = self.soup.find("div", {"class" : "articleBody"})
            self.remove_tag(mainsoup,'div','id','sbchnnLstng')
            self.remove_tag(mainsoup,'img')
            self.remove_tag(mainsoup,'iframe')
            self.remove_tag(mainsoup,'object')
            self.remove_tag(mainsoup,'h1')
            self.remove_tag(mainsoup,'h2')
            self.remove_tag(mainsoup,'h4')
            comments = self.soup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]

            text = self.extract_genenraltext(mainsoup)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'&.*?;', ' ', text)
            self.candidates[i].append(text)
  
class CurataRSSParser(AINewsParser):
    """
    RSS parser for Curata
    e.g. http://ai.curatasite.com/api/v1/articles.rss
    """
    def parse_sourcepage(self, rss_url):
        f = feedparser.parse(rss_url)
        for entry in f.entries:
            d = date(entry.published_parsed[0], \
                    entry.published_parsed[1], entry.published_parsed[2])
            #if d > self.today or d < self.begindate: continue
            
            url = entry.link
            title = entry.title
            self.candidates.append([url, title, d])
                
    def parse_storypage(self):
        for i, candidate in enumerate(self.candidates):
            res = self.parse_url(candidate[0])
            if not res or self.url == None:
                continue
            m = re.search('(http://ai.curatasite.com/articles/share/\d+/)', self.html, re.MULTILINE)
            if m:
                second_url = m.group(1)
            else:
                continue

            res = self.parse_url(second_url)
            if not res or self.url == None or self.db.isindexed(self.url):
                continue
            m = re.search('window.location.href = "(.*?)";', self.html, re.MULTILINE)
            if m:
                real_url = m.group(1)
            else:
                continue

            res = self.parse_url(real_url)
            if not res or self.url == None or self.db.isindexed(self.url):
                continue
            text = self.justext_extract(self.html)
            if len(text) == 0: continue
            self.candidates[i].append(text)
