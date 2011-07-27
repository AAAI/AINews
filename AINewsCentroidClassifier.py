"""
AINewsCentroidClassifier aims to use Rocchio/Centroid-based classification[1] 
to train and predict 19 AI news categories. 

The classification task used to be performed by AINewsTopic.py, but it is a 
 rather simply method.

The training data is 289 manually scrutinized articles for 19 categories.
However, it is very easy to add new articles by simply put them into the
training data directory and re-train the centroid classifier.

[1] Eui-Hong Han, George Karypis, Centroid-Based Document Classification:
Analysis & Experimental Results

Date: Dec.22th, 2010
Author: Liang Dong
"""

import os
import sys
import math
import random
import operator
from subprocess import *
import time
from datetime import date, datetime, timedelta

from AINewsCorpus import AINewsCorpus
from AINewsTools import loadfile2, savefile, savepickle, loadpickle, loadfile
from AINewsConfig import config, paths


class AINewsCentroidClassifier:
    def __init__(self, corpus = None):
        '''
        Initialization of centroid classifier for 19 AI-topic 
        '''
        period = int(config['ainews.period'])
        self.begindate = date.today() - timedelta(days = period)
        self.models = {}
        if corpus != None:
            self.corpus = corpus
        else:
            self.corpus = AINewsCorpus()

    ##############################
    #
    #           Train 
    #
    ##############################
    def train(self, category=None):
        '''
        Training procedures for all 19 centroids 
        It takes in 19 topics' training data from the src_dir,
        and outputs centroid of each topic into dest_dir.
        If category is not None, then only train that specific category.
        '''
        if category == None:
            #print "\n****** Inserting category article word freqs ******\n"
            sql = '''select u.urlid, u.content from cat_corpus as u'''
            rows = self.db.selectall(sql)
            urlids = []
            i = 0
            for row in rows:
                #print "%d/%d" % (i, len(rows))
                i += 1
                urlids.append(row[0])
                wordfreq = self.txtpro.whiteprocess(row[0], row[1])
                self.add_freq_index(wordfreq)
            self.commit_freq_index('wordlist')
                
            for category in self.corpus.categories:
                self.train_centroid(category, urlids, 'centroid')
        else:
            self.train_centroid(category)
        
    def train_centroid(self, category, corpus, model_dir, debug = False):
        '''
        Train only one centroid of given category.
        Given the input training data in the src_dir, and output centroid
        saved as pickle file in the dest_dir.
        '''
        if debug:
            print "\n****** Training", category,"******"
            print "(1) Getting articles"
        corp = []
        for c in corpus:
            if category in c[2].split(' '):
                if debug:
                    print c[0],
                corp.append(c)
        if debug:
            print
            print "(2) Making centroid"
        centroid = self.make_centroid(corp)
        if debug:
            print "(3) Saving centroid",
        savepickle(paths['ainews.category_data']+model_dir+'/'+category+'.pkl',
                centroid)
        
    def make_centroid(self, corpus):
        '''
        Build centroid of one category
        '''
        centroid = {} # will hold final centroid tfidf, indexed by wordid
        for c in corpus:
            data = self.corpus.get_tfidf(c[0], c[1])
            for word in data:
                centroid.setdefault(word, 0.0)
                centroid[word] += data[word]

        distsq = 0.0
        for word in centroid:
            distsq += centroid[word]*centroid[word]

        # Normalize centroid
        dist = math.sqrt(distsq)
        if dist > 1.0e-9:
            for key in centroid:
                centroid[key] /= dist
            
        return centroid
    
    
    ##############################
    #
    #           Predict 
    #
    ##############################
    def init_predict(self, model_dir = None):
        '''
        Initialization prediction by loading 19 centroids from the directory.
        @param  model_dir: 19 centroid models path dir
        @type  model_dir: C{string}
        '''
        self.models = {}
        if model_dir != None:
            for category in self.corpus.categories:
                file = os.path.join(model_dir, category+".pkl")
                self.models[category] = loadpickle(file)

    def predict(self, urlid, wordfreq):
        '''
        Predict its category from the 19 centroids
        Given a urlid of news story, retrieve its saved term vector and
        compare it with 19 category's centroid. Choose the closest category
        as the news story's category/topic.
        '''
        data = self.corpus.get_tfidf(urlid, wordfreq)
        max_sim = 0
        max_cat = ""
        similarities = {}
        for cat in self.models:
            sim = self.corpus.cos_sim(data, self.models[cat], cat)
            similarities[cat] = sim
            if sim > max_sim:
                max_sim = sim
                max_cat = cat
        return (max_cat, similarities)

    def choose_category(self, urlid):
        '''
        Predict and set the article's category.
        '''
        meta = loadpickle(paths['ainews.news_data']+'meta/'+str(urlid)+'.pkl')
        text = loadpickle(paths['ainews.news_data']+'text/'+str(urlid)+'.pkl')
        wordfreq = self.txtpro.whiteprocess(urlid, text)
        (topic, topicsims) = self.predict(urlid)
        # Add topicsims to meta
        meta = (meta[0], meta[1], meta[2], meta[3], topicsims, topic)
        savepickle(paths['ainews.news_data']+'meta/'+str(urlid)+'.pkl', meta)

        print "Choosing category %s for urlid %d (%s)" % \
            (topic, urlid, meta[2])

        # Update category ('topic') in database
        sql = "update urllist set topic = '%s' where rowid = %d" % (topic, urlid)
        self.db.execute(sql)

    def get_candidates(self):
        """
        Get all news candidates during the candidate period.
        @return: a list of candidate news' urlid
        @rtype: C{list}
        """
        sql = """select rowid from urllist where pubdate >= '%s' and topic <> 'NotRelated' 
                 order by rowid asc""" % self.begindate
        rows = self.db.selectall(sql)
        urlids = [row[0] for row in rows]
        return urlids

    def categorize_all(self):
        self.init_predict(paths['ainews.category_data'] + 'centroid')
        candidate_urlids = self.get_candidates()
        for urlid in candidate_urlids:
            self.choose_category(urlid)

    ##############################
    #
    #           Evaluate
    #
    ##############################

    def run(self, predict_corpus):
        count_matched = 0
        for c in predict_corpus:
            (topic, topicsims) = self.predict(c[0], c[1])
            if topic in c[2].split(' '):
                sys.stdout.write('+')
                count_matched += 1
            else:
                sys.stdout.write('.')
            sys.stdout.flush()
        return (100.0*float(count_matched) / float(len(predict_corpus)))

    def evaluate(self, ident):
        '''
        Train on a portion of the corpus, and predict the rest;
        evaluate performance. Various parameters are evaluated.
        @param model_dir: temporary directory to store centroids
        @type model_dir: C{string}
        '''
        random.seed()
        results = {}
        iteration = 0
        iterations = 4 * 3 * 5 * 5 * 5
        for it in range(0, 4):
            for i in range(5, 10, 2):
                pct = i/10.0
                (train_corpus, predict_corpus) = \
                        self.corpus.load_corpus(ident, pct, True)
                for category in self.corpus.categories:
                    self.train_centroid(category, train_corpus, 'centroid_eval', True)
                print
                # init_predict here to establish newly trained models
                self.init_predict(paths['ainews.category_data']+'centroid_eval/')

                for icsd_pow in range(0, 5):
                    for csd_pow in range(0, 5):
                        for sd_pow in range(0, 5):
                            iteration += 1
                            self.corpus.icsd_pow = 1.0 - icsd_pow * 0.5
                            self.corpus.csd_pow = 1.0 - csd_pow * 0.5
                            self.corpus.sd_pow = 1.0 - sd_pow * 0.5
                            rkey = "%d%%, icsd=%.2f, csd=%.2f, sd=%.2f" % \
                                    (10*i, self.corpus.icsd_pow, \
                                    self.corpus.csd_pow, self.corpus.sd_pow)
                            results.setdefault(rkey, [])
                            result = self.run(predict_corpus)
                            results[rkey].append(result)
                            print
                            print ("%d/%d - Matched (%s): %f%%") % \
                                (iteration, iterations, rkey, result)
        print
        print "Summary:"
        for rkey in sorted(results.keys()):
            mean, std = meanstdv(results[rkey])
            print ("%s matched avg %f%% (std dev %f%%)") % \
                (rkey, mean, std)
            print results[rkey]
            print

        print "icsd:"
        for (word,val) in (sorted(self.icsd.iteritems(),
                key=operator.itemgetter(1), reverse=True))[0:10]:
            print "%s: %.2f" % (word, val),
        print
        print "csd:"
        for cat in self.csd:
            print cat
            for (word,val) in (sorted(self.csd[cat].iteritems(),
                    key=operator.itemgetter(1), reverse=True))[0:10]:
                print "%s: %.2f" % (word, val),
            print
            print
        print
        print "sd:"
        for (word,val) in (sorted(self.sd.iteritems(),
                key=operator.itemgetter(1), reverse=True))[0:10]:
            print "%s: %.2f" % (word, val),
        print


"""
Calculate mean and standard deviation of data x[]:
    mean = {\sum_i x_i \over n}
    std = sqrt(\sum_i (x_i - mean)^2 \over n-1)
"""
def meanstdv(x):
    from math import sqrt
    n, mean, std = len(x), 0, 0
    for a in x:
        mean = mean + a
    mean = mean / float(n)
    for a in x:
        std = std + (a - mean)**2
    std = sqrt(std / float(n-1))
    return mean, std

if __name__ == "__main__":
    start = datetime.now()
    
    cat = AINewsCentroidClassifier()

    if len(sys.argv) < 2:
        print ("Provide 'train' or 'evaluate db:cat_corpus:cat_corpus_cats'" +
            " or 'evaluate file:oh10'")
        sys.exit()
    
    if sys.argv[1] == "train":
        cat.train()
    elif sys.argv[1] == "evaluate":
        cat.evaluate(sys.argv[2])
        
    print "\n\n"
    print datetime.now() - start   

