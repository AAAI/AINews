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
from datetime import datetime
from subprocess import *
from AINewsConfig import paths
from AINewsCorpus import AINewsCorpus

class AINewsSVMAnalyzer:
    def __init__(self):
        self.corpus = AINewsCorpus()
        self.categories = self.corpus.categories

    def model_word_weights(self, category):
        f = open(paths['svm.svm_data']+category+'.model', 'r')
        lines = f.readlines()
        f.close()
        labels = re.match('label (-?1) (-?1)', lines[5]).group(1,2)
        if labels[0] == '1': pos_label = 0
        else: pos_label = 1

        cmd = './svm-weight -f %d %s%s.model' % \
                (len(self.corpus.wordids), paths['svm.svm_data'], category)
        (stdout, _) = Popen(cmd, shell = True, stdout = PIPE).communicate()
        weights = {}
        for (wordid,weight) in re.findall('(\d+):(\S+)', stdout):
            weight = float(weight)
            if pos_label == 1: weight = -weight
            weights[self.corpus.wordids[int(wordid)]] = weight
        return weights

    def analyze_all(self):
        for cat in self.categories:
            weights = analyzer.model_word_weights(cat)
            weights_sorted = sorted(weights.items(), key=operator.itemgetter(1))
            print "**%s**" % cat
            print "--Least significant:"
            for (word, weight) in weights_sorted[0:10]:
                print ("%s: %.3f, " % (word, weight)),
            print
            print "--Most significant:"
            for (word, weight) in weights_sorted[-10:]:
                print ("%s: %.3f, " % (word, weight)),
            print
            print

if __name__ == "__main__":
    analyzer = AINewsSVMAnalyzer()
    analyzer.analyze_all()

