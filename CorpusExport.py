# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

import sys
import re
from AINewsConfig import paths
from AINewsCorpus import AINewsCorpus
from AINewsCentroidClassifier import AINewsCentroidClassifier

aicorpus = AINewsCorpus()

def dissim(tfidf1, tfidf2, category = None):
    d = 1.0 - aicorpus.cos_sim(tfidf1, tfidf2, category)
    if d < 0.1E-10: d = 0.0
    return d

if __name__ == "__main__":

    directory = sys.argv[1]
    ident = sys.argv[2]

    corpus = aicorpus.load_corpus(ident, 1.0)[0]

    centroid = AINewsCentroidClassifier(aicorpus)
    for category in aicorpus.categories:
        centroid.train_centroid(category, corpus, 'centroid_eval', True)
    centroid.init_predict(paths['ainews.category_data'] + 'centroid_eval')

    aicorpus.icsd_pow = 0.0
    aicorpus.csd_pow = 0.0
    aicorpus.sd_pow = 0.0

    models = {}
    for cat in aicorpus.categories:
        models[cat] = []

    articles = {}
    cache = {}

    for c in corpus:
        for cat in c[2].split(' '):
            tfidf = aicorpus.get_tfidf(int(c[0]), c[1])
            articles[c[0]] = (tfidf, cat)
            models[cat].append(c[0])

    models_csv = open("%s/models.csv" % directory, 'w')
    ms = sorted(models.keys())
    for model in ms:
        models_csv.write(model)
        if model != ms[-1]: models_csv.write(",")
    models_csv.write("\n")
    for model in ms:
        models_csv.write(model + ",")
        for other in ms:
            d = dissim(centroid.models[model], centroid.models[other], model)
            models_csv.write(str(d))
            if other != ms[-1]: models_csv.write(",")
        models_csv.write("\n")
    models_csv.close()

    for model in models:
        model_csv = open("%s/%s.csv" % (directory, model), 'w')
        urlids = sorted(models[model])
        model_csv.write(model + ",")
        for urlid in urlids:
            model_csv.write(str(urlid) + " " + model)
            if urlid != urlids[-1]: model_csv.write(",")
        model_csv.write("\n")
        model_csv.write(model + ",0.0,")
        for urlid in urlids:
            d = dissim(articles[urlid][0], centroid.models[model], model)
            cache[(model, urlid)] = d
            model_csv.write(str(d))
            if urlid != urlids[-1]: model_csv.write(",") 
        model_csv.write("\n")
        for urlid in urlids:
            model_csv.write(str(urlid) + " " + model + ",")
            model_csv.write(str(cache[(model, urlid)]) + ",")
            for other in urlids:
                if (urlid, other) in cache:
                    model_csv.write(str(cache[(urlid, other)]))
                elif (other, urlid) in cache:
                    model_csv.write(str(cache[(other, urlid)]))
                else:
                    tfidf_article = articles[urlid][0]
                    tfidf_other = articles[other][0]
                    d = dissim(tfidf_article, tfidf_other, model)
                    cache[(urlid, other)] = d
                    model_csv.write(str(d))
                if other != urlids[-1]: model_csv.write(",")
            model_csv.write("\n")
        model_csv.close()

    corpus_csv = open("%s/corpus.csv" % directory, 'w')
    urlids = sorted(articles.keys())
    for urlid in urlids:
        corpus_csv.write(str(urlid) + " " + articles[urlid][1])
        if urlid != urlids[-1]: corpus_csv.write(",")
    corpus_csv.write("\n")
    for urlid in urlids:
        corpus_csv.write(str(urlid) + " " + articles[urlid][1] + ",")
        for other in urlids:
            if (urlid, other) in cache:
                corpus_csv.write(str(cache[(urlid, other)]))
            elif (other, urlid) in cache:
                corpus_csv.write(str(cache[(other, urlid)]))
            else:
                tfidf_article = articles[urlid][0]
                tfidf_other = articles[other][0]
                d = dissim(tfidf_article, tfidf_other, articles[urlid][1])
                cache[(urlid, other)] = d
                corpus_csv.write(str(d))
            if other != urlids[-1]: corpus_csv.write(",")
        corpus_csv.write("\n")
    corpus_csv.close()

