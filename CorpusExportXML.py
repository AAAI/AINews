# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

import sys
import re
import operator
import urllib2
import time
from AINewsConfig import blacklist_words
from AINewsCorpus import AINewsCorpus
from AINewsSummarizer import AINewsSummarizer

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)

def urlopen_with_retry(url):
    tries = 0
    u = None
    while tries < 4:
        print >> sys.stderr, "try %d to %s" % (tries, url)
        tries += 1
        try:
            u = urllib2.urlopen(url, None, 5)
            break
        except IOError:
            time.sleep(1)
    return u

aicorpus = AINewsCorpus()
summarizer = AINewsSummarizer()

print "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
print "<news>"

all_articles = aicorpus.get_articles_idrange(322, 10000000)

print "<!--",len(all_articles),"-->"

for urlid in all_articles:
    article = all_articles[urlid]

    if article["pubdate"] == None: continue

    print >> sys.stderr, "urlid %d" % urlid

    categories = []
    for cat in article["categories"]:
        if cat == "Applications":
            categories.append("Application Areas")
        elif cat == "Games":
            categories.append("Games &amp; Puzzles")
        elif cat == "Systems":
            pass
        elif cat == "AIOverview":
            categories.append("AI Overview")
        elif cat == "Ethics":
            categories.append("Ethics &amp; Social Issues")
        elif cat == "Representation" or cat == "Reasoning":
            categories.append("Representation &amp; Reasoning")
        elif cat == "Agents":
            pass
        elif cat == "Education":
            categories.append("Intelligent Tutoring")
        elif cat == "Systems":
            categories.append("Systems &amp; Languages")
        else:
            cat = re.sub(r'([a-z])([A-Z])', r'\1 \2', cat)
            categories.append(cat)

    if len(categories) == 0: continue

    found_blacklist_word = False
    for word in blacklist_words:
        if re.search("\W%s\W" % word, article["content_all"], re.IGNORECASE) != None:
            found_blacklist_word = True
            break
    if found_blacklist_word: continue
    
    aitopics_url = "http://aitopics.net/AIArticles/%d-%s?action=markdown" % \
        (article["pubdate"].year, article["urlid"])
    f = urlopen_with_retry(aitopics_url)
    if f is None: continue
    try:
        content = f.read()
    except:
        continue
    m = re.match(r".*(Whitelist words:.*?)\s+Duplicates.*", content, re.DOTALL)
    if m: newsfinder_output = re.sub(r'<', '&lt;', re.sub(r'>', '&gt;', m.group(1)))
    else: newsfinder_output = ""

    if re.match(r"^http://news\.google\.com", article["url"]):
        url = re.sub(r"^http://news\.google\.com/news/url\?.*&url=(.*)$", r'\1', article["url"])
    else:
        url = article["url"]

    if article["summary"] == "":
        summary = " ".join(summarizer.summarize_single_ots(article))
    else:
        summary = article["summary"]

    print "<article>"
    print "\t<guid>news%s</guid>" % urlid
    print "\t<title>%s</title>" % html_escape(article["title"])
    print "\t<summary>%s</summary>" % html_escape(summary)
    print "\t<crawldate>%s</crawldate>" % article["crawldate"]
    print "\t<topics>%s</topics>" % ",".join(categories)
    print "\t<url>%s</url>" % html_escape(url)
    print "\t<publisher>%s</publisher>" % html_escape(article["publisher"])
    print "\t<pubdate>%s</pubdate>" % article["pubdate"]
    print "\t<tfpn>%s</tfpn>" % article["tfpn"]
    print "\t<pubyear>%s</pubyear>" % article["pubdate"].year
    if article["published"]:
        print "\t<published>1</published>"
    else:
        print "\t<published>0</published>"
    print "\t<newsfinder>%s</newsfinder>" % newsfinder_output
    print "\t<content>%s</content>" % html_escape(article["content_all"])
    print "</article>"

print "</news>"

