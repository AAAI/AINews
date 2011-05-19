"""
AINewsTools provides a set of helper functions to manage save/load files
and html/text processing.
"""
import os
import sys
import re
import csv
import string
import pickle
import locale
import ConfigParser



def nukedir(dir):
    """
    Delete all files and remove directory.
    @param dir: target directory to be removed
    @type dir:C{string}
    """
    if dir[-1] == os.sep: dir = dir[:-1]
    files = os.listdir(dir)
    for file in files:
        if file == '.' or file == '..': continue
        path = dir + os.sep + file
        if os.path.isdir(path):
            nukedir(path)
        else:
            os.unlink(path)
        

def savefile(filename, content):
    """
    Helper function to save content into file.
    @param filename: target file's name
    @type filename: C{string}
    @param content: the content to be saved into the file
    @type content: C{string}
    """
    
    try:
        f = open(filename , "w")
    except IOError , e:
        print >> sys.stderr, "Fail to save file %s: %s" % (filename, e)
    else:
        f.write(content)
        f.close()
        
def loadfile(filename):
    """
    Helper function to load content given the filename
    @param filename: target file's name
    @type filename: C{string}
    """
    try:
        f = open(filename , "r")
    except IOError , e:
        print >> sys.stderr, "Fail to load file %s: %s" % (filename, e)
        return []
    else:
        lines = f.readlines()
        f.close()
        return lines

def loadfile2(filename):
    """
    Helper function to load content given the filename
    @param filename: target file's name
    @type filename: C{string}
    """
    try:
        f = open(filename , "r")
    except IOError , e:
        print >> sys.stderr, "Fail to load file %s: %s" % (filename, e)
        return ""
    else:
        content = f.read()
        f.close()
        return content
    
def loadpickle(filename):
    """
    Helper function to load content by Python's Pickle module.
    @param filename: target file's name
    @type filename: C{string}
    """
    pkl_file = open(filename, 'rb')
    content = pickle.load(pkl_file)
    pkl_file.close()
    return content

def savepickle(filename, content):
    """
    Helper function to save content into file.
    @param filename: save content into target file's name
    @type filename: C{string}
    @param content: the content to be saved
    @type content: C{string}
    """
    output = open(filename, 'wb')
    pickle.dump(content, output)
    output.close()
    
def loadcsv(filename):
    """
    Read csv files and return rows
    @param filename: target file's name
    @type filename: C{string}
    """
    rows = []
    try:
        file = open(filename, 'r')
    except IOError , e:
        print "Fail to csv file because of %s" % e
    else:
        for row in csv.reader(file):
            rows.append(row)
        file.close()
    return rows

def unescape(url):
    """
    The url retrieved from MySQL database has extra slash('\') for all the
    punctuations.
    @param url: the url string to be unescaped
    @type url: C{string}
    """
    return re.sub(r'\\(.)', r'\1', url)    

def loadconfig(filename, config={}):
    """
    Helper function to readin the content from config.ini and
    returns a dictionary with key's of the form
    <section>.<option> and the values
    @param filename: target file's name
    @type filename: C{string}
    @param config: extra configuration content
    @type config: C{dict}
    """
    config = config.copy()
    cp = ConfigParser.ConfigParser()
    cp.read(filename)
    for sec in cp.sections():
        name = string.lower(sec)
        for opt in cp.options(sec):
            config[name + "." + string.lower(opt)] = \
                                                string.strip(cp.get(sec, opt))
    return config

def loadpmwiki(filename):
    """
    Deprecated.
    Load Pmwiki page from wiki.d directory and extract contents.
    """
    lines = loadfile(filename)
    page = {}
    for line in lines:
        pos = re.search("=", line)
        if pos != None:
            page[line[:pos.start()]] = line[pos.end():]
    return page

def savepmwiki(filename, page):
    """
    Deprecated.
    Save Pmwiki page from wiki.d directory
    """
    content = ""
    for key in page.keys():
        content += key + '=' + page[key]
    savefile(filename, content)
        
def strip_html(html):
    """
    Helper function to quickly remove all the <> tags from the html code.
    @param html: target raw html code
    @type html: C{string}
    """
    res = ''
    start = 0
    for char in html:
        if char == '<':
            start = 1
        elif char == '>':
            start = 0
            res += ' '
        elif start == 0:
            res += char
    return res

def getwords(raw):
    """
    Helper function to extract bag of words from the raw text.
    @param raw: target raw text
    @type raw: C{string}
    """
    if raw =="": return []
    splitter=re.compile('\\W*')
    return [s.lower() for s in splitter.split(raw) if s != '']


def loadstoplist():
    """
    Load the stoplist to remove most common words
    """
    words = set()
    try:
        file = open("resource/stoplist.txt", "r")
    except IOError:
        print "Fail to open stop-list file"
    else:
        for word in file.readlines():
            words.add(word.rstrip())
        file.close()
    return words
