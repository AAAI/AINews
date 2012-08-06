# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

from operator import itemgetter
from subprocess import *
import sys
import os
import nltk

from AINewsConfig import stopwords, paths
from AINewsCorpus import AINewsCorpus

class AINewsSummarizer:
    def __init__(self):
        self.sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

    def reorder_sentences(self, output_sentences, content):
        output_sentences.sort(lambda s1, s2:
            content.find(s1) - content.find(s2))
        return output_sentences

    def summarize_single_ots(self, article):
        f = open(paths['ainews.output'] + 'content.txt', 'w')
        f.write(article['content'])
        f.close()
        (stdout, _) = Popen("%s -r 30 %s" % (paths['libraries.ots'], (paths['ainews.output'] + 'content.txt')), \
                                shell = True, stdout=PIPE).communicate()
        sentences = self.sent_detector.tokenize(stdout)
        return sentences[:4]

    def summarize(self, corpus, articles):
        for urlid in articles:
            articles[urlid]['summary'] = \
                (" ".join(self.summarize_single_ots(articles[urlid]))).strip()
    
