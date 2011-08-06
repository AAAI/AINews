"""
The base parser class for extracting text for general news story.
The urllib2 and urlparse are used to download the HTML pages from the website.
It utilizes BeautifulSoup library for HTML parsing. It extracts the creation
date, title, description, and text from the HTML content.

The general noisy removeal algorithm is based on counting the ratio of
hyperlinked words # VS total words #. If the ratio is greater than certain
threshold, the HTML block is consider noisy block such as menu, advertisement...

It is the base class for the specific parsers in AINewsSourceParser.py.
"""

import re
import sys
import time
import urllib2
import urlparse
from datetime import date, datetime, timedelta
from BeautifulSoup import BeautifulSoup, Comment, BeautifulStoneSoup, \
                NavigableString, Declaration, ProcessingInstruction
from AINewsDB import AINewsDB
from AINewsConfig import config, paths, dateformat_regexps

sys.path.append(paths['libraries.tools'])
import justext

class AINewsParser:
    def __init__(self):
        self.today = date.today()
        self.link_density = config['parser.link_density_ratio']
        self.debug = config['ainews.debug']
        self.db = AINewsDB()
        period = int(config['ainews.period'])
        self.begindate = self.today - timedelta(days = period)
        self.clear()
        self.candidates = []

    def justext_extract(self, html):
        good_pars = []
        pars = justext.justext(html, justext.get_stoplist('English'))
        for par in pars:
            if par['class'] == 'good':
                good_pars.append(par['text'])
        return "\n".join(good_pars)
        
    def clear(self):
        self.url = ""
        self.html = None
        self.soup = None
        self.title = ""
        self.description = ""
        self.text = ""
        self.pubdate = None
        
    def parse_url(self, url):
        """
        Using urllib2 to parse url and retrieve HTML code from the given url.
        @param url: Target url news story to be parsed.
        @type url: C{string}
        """
        self.clear()
        agent = config['ainews.agent_name']+'/'+config['ainews.version']
        try:
            request  = urllib2.Request(url)
            request.add_header('User-Agent', agent)
            opener = urllib2.build_opener()
            response = opener.open(request)
        except urllib2.HTTPError, error:
            if self.debug:
                if error.code == 404:
                    print >> sys.stderr, "HTTPERROR: %s -> %s" % (error, error.url)
                elif error.code == 403:
                    print >> sys.stderr, "HTTPERROR: %s -> %s" % (error, error.url)
                else :
                    print >> sys.stderr, "HTTPERROR: %s" % error
            return False
        except urllib2.URLError, error:
            if self.debug: print >> sys.stderr, "URLERROR: %s" % error
            return False
        except Exception, error:
            if self.debug: print >> sys.stderr, "ERROR: %s" % error
            return False
        
        url = response.geturl()
        self.url = url.split('#')[0] # Remove in-page anchor link
        self.html = response.read()
        return True
    
    def extract_content(self, extractdate = False):
        """
        Using BeautifulSoup to parse HTML and extract metadata and
        news text.
        @param extractdate: Flag for whether run the date-extraction part
        @type extractdate: C{boolean}
        """
        try:
            self.soup = BeautifulSoup(self.html, \
                        convertEntities = BeautifulStoneSoup.HTML_ENTITIES)
        except Exception, error:
            #if self.debug: print >> sys.stderr, "SOUP ERROR: %s" % error
            return False
            
        ################################################################
        #         Extract title from HTML code
        ################################################################
        head = self.soup.find('head')
        if head != None:
            title = head.find('title')
            if title != None:
                title = (title.string).encode('utf-8')
                self.title = re.sub(r'\s+', ' ', title)
        
        ################################################################
        #         Extract meta description from HTML code
        ################################################################
        description = self.soup.find('meta', {'name':'description'})
        if description != None and description.has_key('content'):
            desc = (description['content']).encode('utf-8')
            desc = re.sub(r'<!--.*?-->', ' ', desc)
            desc = re.sub(r'<.*?>', ' ', desc)
            desc = re.sub(r'&.*?;', ' ', desc)
            self.description = re.sub(r'\s+', ' ', desc)
            
        ################################################################
        #         Extract meta published (created) date from HTML code
        ################################################################
        if extractdate:
            self.pubdate = None
            metas = self.soup.findAll('meta')
            for meta in metas:
                if meta.has_key('name')  \
                    and re.search('date|create|time', meta['name'], \
                                  re.IGNORECASE)!= None:
                    self.pubdate = self.extract_date(meta['content'])
                    if self.pubdate != None: break

            if self.pubdate == None:                    
                self.pubdate = self.extract_date(self.html)
            if self.pubdate == None:
                self.pubdate = date.today()
                    
        ################################################################
        #   Remove all the comments, javascripts, css styles, iframes...
        ################################################################
        
        comments = self.soup.findAll(text=lambda text:isinstance(text, Comment))
        [comment.extract() for comment in comments]
        declarations = self.soup.findAll(text=lambda \
                                         text:isinstance(text, Declaration))
        [declaration.extract() for declaration in declarations]
        instructions = self.soup.findAll(text=lambda \
                                text:isinstance(text, ProcessingInstruction))
        [instruction.extract() for instruction in instructions]
        
        headers = self.soup.findAll('head')
        [header.extract() for header in headers]
        
        scripts = self.soup.findAll('script')
        [script.extract() for script in scripts]
        noscripts = self.soup.findAll('noscript')
        [noscript.extract() for noscript in noscripts]
        
        styles = self.soup.findAll('style')
        [style.extract() for style in styles]
        
        links = self.soup.findAll('link')
        [link.extract() for link in links]
        
        iframes = self.soup.findAll('iframe')
        [iframe.extract() for iframe in iframes]
        
        selects =  self.soup.findAll('select')
        [select.extract() for select in selects]
        
        doctypes =  self.soup.findAll('!DOCTYPE')
        [doctype.extract() for doctype in doctypes]
        
        labels = self.soup.findAll('label')
        [label.extract() for label in labels]
        
        # Remove embeded video and audio        
        objects = self.soup.findAll('object')
        [object.extract() for object in objects]
        
        # Remove images
        imgs = self.soup.findAll('img')
        [img.extract() for img in imgs]
        
        ################################################################
        #      Extact the major news text content from HTML code by
        # calling traverse() to remove noisy HTML blocks by link density
        ################################################################
        self.traverse(self.soup)
       
        text = self.extract_genenraltext(self.soup)
        
        # Use regular expression to filter extra comments and tags   
        text = re.sub(r'<!--.*?-->', ' ', text)
        text = re.sub(r'<.*?>', ' ', text)
        
        text = re.sub(r'\s+', ' ', text)
        self.text = text.encode('utf-8')
        
        return True

    def extract_genenraltext(self, mysoup):
        """
        Recursively extract text from a BeautifulSoup object.
        @param mysoup: the target BeautifulSoup object to be extracted
        @type mysoup: C{BeautifulSoup}
        """
        if mysoup == None: return "\n"
        if  isinstance(mysoup,NavigableString):
            return mysoup.string
        else:
            text = ""
            for subelement in mysoup.contents:
                text += self.extract_genenraltext(subelement)
            return text    
    ''' 
    def extract_genenraltext(self, mysoup):
        """
        Recursively extract text from a BeautifulSoup object.
        @param mysoup: the target BeautifulSoup object to be extracted
        @type mysoup: C{BeautifulSoup}
        """
        if mysoup == None: return ""
        if type(mysoup) == NavigableString:
            return mysoup.string.strip()
        else:
            text = ""
            for subelement in mysoup.contents:
                text += self.extract_genenraltext(subelement)+' '
            return text.strip()
    '''    
    def extract_linktext(self, mysoup):
        """
        Extract all the text which are hyperlinked from a BeautifulSoup object.
        @param mysoup: the target BeautifulSoup object to be extracted
        @type mysoup: C{BeautifulSoup}
        """
        text = ""
        if type(mysoup) == NavigableString:
            return ""
        else:
            hyperlinks = mysoup.findAll('a')
            for hyperlink in hyperlinks:
                text += self.extract_genenraltext(hyperlink)+' '
            return text.strip()
            
    def getwords(self, raw):
        if raw == "": return []
        return re.split(r'\W+',raw)
        
    def traverse(self, mysoup):
        """
        Traverse the beautifulsoup and iteratively remove noisy HTML blocks 
        based on link-word density.
        @param mysoup: the target BeautifulSoup object 
        @type mysoup: C{BeautifulSoup}
        """
        if type(mysoup) != NavigableString and len(mysoup.contents)>0:
            subelement = mysoup.contents[0]
            while(subelement != None):
                gt = self.extract_genenraltext(subelement)
                word_count = len(self.getwords(gt))
                if word_count == 0:
                    next = subelement.nextSibling 
                    subelement.extract()  # Remove subelement from the soup
                    subelement = next
                    continue
                lt = self.extract_linktext(subelement)
                linkword_count = len(self.getwords(lt))
                ratio = 1.0*linkword_count/word_count
                
                if ratio >= self.link_density:
                    next = subelement.nextSibling 
                    subelement.extract()  # Remove subelement from the soup
                    subelement = next
                else:
                    self.traverse(subelement)
                    subelement = subelement.nextSibling 

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
    
    def parse_date(self, date_str, dateformat):
        """
        Given a string of date and a date format, return a date object
        @param date_str: Target date text
        @type date_str: C{string}
        @param dateformat: regular expression of the date format
        @type dateformat: C{string}
        """
        t = time.strptime(date_str,dateformat_regexps[dateformat][1])
        d = date(t[0], t[1], t[2])
        return d
    
    def print_content(self):
        print "\n*** Title *** \n\t", self.title
        print "\n*** URL *** \n\t", self.url
        print "\n*** Meta Description ***\n\t", self.description
        print "\n*** Body Text ***\n\t", self.text
        print "\n*** Publish Date ***\n\t", self.pubdate
        
    def remove_tag(self, soup, name, attr=None, value=None):
        if attr!=None:
            tags = soup.findAll(name, {attr:value})
        else:
            tags = soup.findAll(name)
        [tag.extract() for tag in tags]
