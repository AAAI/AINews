
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

def model_to_csv(model, max_key):
    csv = ""
    for i in range(1, max_key + 1):
        if i in model: csv += str(model[i])
        else: csv += "0.0"
        csv += ","
    return csv[:-1] # drop last ","

if __name__ == "__main__":

    limit = int(sys.argv[1])

    classifier = AINewsCentroidClassifier()
    classifier.init_predict(None, 'wordlist_eval')

    db = AINewsDB()

    #txtpro = AINewsTextProcessor()

    #rows = list(db.selectall("""select c.urlid, c.content, cc.category
    #            from cat_corpus as c, cat_corpus_cats as cc
    #            where c.urlid = cc.urlid"""))
    rows = classifier.load_corpus("/home/josh/AINews/corpus/other/text-data", "oh10")
    random.shuffle(rows)
    random.shuffle(rows)

    corpus = rows[:limit]
    #corpus = []
    #for c in rows[:limit]:
    #    wordfreq = txtpro.simpletextprocess(c[0], c[1])
    #    if wordfreq.N() > 0:
    #        corpus.append(c)
    classifier.corpus_count = len(corpus)

    db.execute("delete from wordlist_eval")
    db.execute("alter table wordlist_eval auto_increment = 0")
    classifier.wordids = {}
    classifier.cache_urls = {}
    
    classifier.tfijk = {}
    classifier.tfik = {}
    for cat in classifier.categories:
        classifier.cat_urlids[cat] = []
    for cat in classifier.categories:
        classifier.tfik[cat] = {}
        classifier.tfijk[cat] = {}
    for c in corpus:
        classifier.cat_urlids[cat].append(c[0])
    for c in corpus:
        #wordfreq = txtpro.simpletextprocess(c[0], c[1])
        classifier.add_freq_index(c[0], c[1], c[2].split())
    classifier.commit_freq_index('wordlist_eval')

    classifier.init_predict(None, 'wordlist_eval')
    for cat in classifier.categories:
        classifier.train_centroid(cat, corpus, 'centroid_eval')
    classifier.init_predict(paths['ainews.category_data']+'centroid_eval/',
            'wordlist_eval')

    classifier.icsd_pow = 0.0
    classifier.csd_pow = 0.0
    classifier.sd_pow = 0.0

    models = {}
    for cat in classifier.categories:
        centroid = load_category(cat)
        if len(centroid) != 0: models[cat] = centroid

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


