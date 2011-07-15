
import os
import math
import sys
import random
import re
from AINewsConfig import paths
from AINewsTools import loadpickle
from AINewsDB import AINewsDB
from AINewsCentroidClassifier import AINewsCentroidClassifier
from AINewsTextProcessor import AINewsTextProcessor

def find_max_key(models):
    maxes = map(lambda m: max(m.keys()), models)
    return max(maxes)

def load_category(category):
    file = paths['ainews.category_data'] + "centroid_eval/" + category + ".pkl"
    return loadpickle(file)

if __name__ == "__main__":

    ident = sys.argv[1]

    classifier = AINewsCentroidClassifier()
    corpus = classifier.load_corpus(ident, 1.0)[0]

    classifier.icsd_pow = 0.0
    classifier.csd_pow = 0.0
    classifier.sd_pow = 0.0

    models = classifier.models

    for c in corpus:
        models["%s %s" % (c[0], c[2])] = classifier.get_tfidf(int(c[0]), c[1])

    cache = {}

    names = sorted(models.keys())
    for name in names:
        print name,
        if name != names[-1]: print ",",
    print
    for name in names:
        print name + ",",
        for other in names:
            if name in classifier.categories:
                urlidA = name
            else:
                urlidA = re.sub(r'[^\d]*', '', name)

            if other in classifier.categories:
                urlidB = other
            else:
                urlidB = re.sub(r'[^\d]*', '', other)

            if (urlidA,urlidB) in cache:
                print str(cache[(urlidA,urlidB)]),
            elif (urlidB,urlidA) in cache:
                print str(cache[(urlidB,urlidA)]),
            else:
                # go from similarity to dissimilarity
                dissim = 1.0 - classifier.cos_sim(models[name], models[other])
                if dissim < 0.1E-10: dissim = 0.0
                cache[(urlidA,urlidB)] = dissim
                print str(dissim),
            if other != names[-1]: print ",",
        print


