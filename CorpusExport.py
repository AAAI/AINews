
import os
import math
import sys
import random
from AINewsConfig import paths
from AINewsTools import loadpickle
from AINewsDB import AINewsDB
from AINewsCentroidClassifier import AINewsCentroidClassifier
from AINewsTextProcessor import AINewsTextProcessor

def find_max_key(models):
    maxes = map(lambda m: max(m.keys()), models)
    return max(maxes)

if __name__ == "__main__":

    limit = int(sys.argv[1])

    classifier = AINewsCentroidClassifier()
    classifier.init_predict(None, 'wordlist_eval')

    db = AINewsDB()

    txtpro = AINewsTextProcessor()

    rows = list(db.selectall("select urlid, content from cat_corpus"))
    random.shuffle(rows)
    corpus = rows[:limit]

    db.execute("delete from wordlist_eval")

    for c in corpus:
        wordfreq = txtpro.textprocess(c[1])
        classifier.add_freq_index(wordfreq)
    classifier.commit_freq_index('wordlist_eval')
    classifier.init_predict(None, 'wordlist_eval')

    models = {}
    for c in corpus:
        models[str(c[0])] = classifier.get_tfidf(int(c[0]), c[1])

    cache = {}

    names = sorted(models.keys())
    for name in names:
        print name,
        if name != names[-1]: print ",",
    print
    for name in names:
        print name + ",",
        for other in names:
            if (name,other) in cache:
                print str(cache[(name,other)]),
            elif (other,name) in cache:
                print str(cache[(other,name)]),
            else:
                # go from similarity to dissimilarity
                dissim = 1.0 - classifier.cos_sim(models[name], models[other])
                if dissim < 0.1E-10: dissim = 0.0
                cache[(name,other)] = dissim
                print str(dissim),
            if other != names[-1]: print ",",
        print


