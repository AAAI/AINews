
import os
import math
import sys
import random
from AINewsConfig import paths
from AINewsTools import loadpickle
from AINewsDB import AINewsDB
from AINewsCentroidClassifier import AINewsCentroidClassifier

def load_category(category):
    file = os.path.join(paths['ainews.category_data'] + "centroid_eval/" + category + ".pkl")
    return loadpickle(file)

def find_max_key(models):
    maxes = [0]
    for model in models:
        if len(model.keys()) > 0:
            maxes.append(max(model.keys()))
    return max(maxes)

def model_to_csv(model, max_key):
    csv = ""
    for i in range(1, max_key + 1):
        if i in model: csv += str(model[i])
        else: csv += "0.0"
        csv += ","
    return csv[:-1] # drop last ","


if __name__ == "__main__":
    categories =["AIOverview","Agents", "Applications", \
                 "CognitiveScience","Education","Ethics", "Games", "History",\
                 "Interfaces","MachineLearning","NaturalLanguage","Philosophy",\
                 "Reasoning","Representation", "Robots","ScienceFiction",\
                 "Speech", "Systems","Vision"]

    db = AINewsDB()
    random.seed()

    urllist = []
    if sys.argv[1] == "corpus":
        urllist = sys.argv[2:]
    elif sys.argv[1] == "all":
        categories = []
        rows = db.selectall("select urlid from cat_corpus")
        for row in rows:
            urllist.append(str(row[0]))
    elif sys.argv[1] == "category":
        categories = [sys.argv[2]]
        rows = list(db.selectall("select urlid from cat_corpus_cats where category='%s'" % sys.argv[2]))
        random.shuffle(rows)
        random.shuffle(rows)
        for row in rows[:int(sys.argv[3])]:
            urllist.append(str(row[0]))

    classifier = AINewsCentroidClassifier()
    classifier.init_predict(paths['ainews.category_data']+'centroid_eval/', 'wordlist_eval')

    models = {}

    for cat in categories:
        c = load_category(cat)
        if len(c) != 0: models[cat] = c

    for urlid in urllist:
        c = db.selectone("select content from cat_corpus where urlid=%s" % urlid)
        if c == None: continue
        tfidf = classifier.get_tfidf(urlid, c[0])
        if len(tfidf) > 0 and reduce(lambda x, y: x + y, tfidf.values()) > 1.0e-9:
            models[urlid] = tfidf
        else:
            pass
            #print urlid
            #print tfidf
            #print c[0]

    max_key = find_max_key(models.values())

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


