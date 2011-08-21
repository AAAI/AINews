# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

import sys
from AINewsDB import AINewsDB

categories =["AIOverview","Agents", "Applications", \
             "CognitiveScience","Education","Ethics", "Games", "History",\
             "Interfaces","MachineLearning","NaturalLanguage","Philosophy",\
             "Reasoning","Representation", "Robots","ScienceFiction",\
             "Speech", "Systems","Vision"]

db = AINewsDB()

url_counts = {}

cat_counts = {}
for cat in categories:
    cat_counts[cat] = 0

rows = db.selectall( \
        "select c.urlid, c.content, group_concat(cc.category separator ' ') " +
        "from cat_corpus as c, cat_corpus_cats as cc where c.urlid = cc.urlid " +
        "group by c.urlid")
for row in rows:
    url_counts[row[0]] = len(row[2].split(' '))
    for cat in row[2].split(' '):
        cat_counts[cat] += 1

if sys.argv[1] == "bar":
    print "Category,Count"
    for cat in sorted(cat_counts.keys(),reverse=True):
        print "%s,%d" % (cat, cat_counts[cat])
elif sys.argv[1] == "hist":
    print "URL,Count"
    for urlid in url_counts:
        print "%d,%d" % (urlid, url_counts[urlid])


    

