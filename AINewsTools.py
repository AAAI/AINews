# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

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
    for key in page:
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


"""Truncation beautifier function
This simple function attempts to intelligently truncate a given string
__author__ = 'Kelvin Wong <www.kelvinwong.ca>'
__date__ = '2007-06-22'
__version__ = '0.10'
__license__ = 'Python http://www.python.org/psf/license/'
"""

def trunc(s,min_pos=0,max_pos=75,ellipsis=True):
    """Return a nicely shortened string if over a set upper limit 
    (default 75 characters)
    
    What is nicely shortened? Consider this line from Orwell's 1984...
    0---------1---------2---------3---------4---------5---------6---------7---->
    When we are omnipotent we shall have no more need of science. There will be
    
    If the limit is set to 70, a hard truncation would result in...
    When we are omnipotent we shall have no more need of science. There wi...
    
    Truncating to the nearest space might be better...
    When we are omnipotent we shall have no more need of science. There...
    
    The best truncation would be...
    When we are omnipotent we shall have no more need of science...
    
    Therefore, the returned string will be, in priority...
    
    1. If the string is less than the limit, just return the whole string
    2. If the string has a period, return the string from zero to the first
        period from the right
    3. If the string has no period, return the string from zero to the first
        space
    4. If there is no space or period in the range return a hard truncation
    
    In all cases, the string returned will have ellipsis appended unless
    otherwise specified.
    
    Parameters:
        s = string to be truncated as a String
        min_pos = minimum character index to return as Integer (returned
                  string will be at least this long - default 0)
        max_pos = maximum character index to return as Integer (returned
                  string will be at most this long - default 75)
        ellipsis = returned string will have an ellipsis appended to it
                   before it is returned if this is set as Boolean 
                   (default is True)
    Returns:
        Truncated String
    Throws:
        ValueError exception if min_pos > max_pos, indicating improper 
        configuration
    Usage:
    short_string = trunc(some_long_string)
    or
    shorter_string = trunc(some_long_string,max_pos=15,ellipsis=False)
    """
    # Sentinel value -1 returned by String function rfind
    NOT_FOUND = -1
    # Error message for max smaller than min positional error
    ERR_MAXMIN = 'Minimum position cannot be greater than maximum position'
    
    # If the minimum position value is greater than max, throw an exception
    if max_pos < min_pos:
        raise ValueError(ERR_MAXMIN)
    # Change the ellipsis characters here if you want a true ellipsis
    if ellipsis:
        suffix = '...'
    else:
        suffix = ''
    # Case 1: Return string if it is shorter (or equal to) than the limit
    length = len(s)
    if length <= max_pos:
        return s + suffix
    else:
        # Case 2: Return it to nearest period if possible
        try:
            end = s.rindex('.',min_pos,max_pos)
        except ValueError:
            # Case 3: Return string to nearest space
            end = s.rfind(' ',min_pos,max_pos)
            if end == NOT_FOUND:
                end = max_pos
        return s[0:end] + suffix

