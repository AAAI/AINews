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
from subprocess import *
import time
from datetime import date, datetime, timedelta

from AINewsDB import AINewsDB
from AINewsTextProcessor import AINewsTextProcessor
from AINewsTools import loadfile2, savefile, savepickle, loadpickle, loadfile
from AINewsConfig import config, paths


class AINewsCentroidClassifier:
    def __init__(self):
        '''
        Initialization of centroid classifier for 19 AI-topic 
        '''
        period = int(config['ainews.period'])
        self.begindate = date.today() - timedelta(days = period)

        self.txtpro = AINewsTextProcessor()
        self.db = AINewsDB()
        self.corpus_count = (self.db.selectone('select count(*) from cat_corpus'))[0]
        self.cache_urls = {}

        self.wordlist = {}

        self.categories =["AIOverview","Agents", "Applications", \
                 "CognitiveScience","Education","Ethics", "Games", "History",\
                 "Interfaces","MachineLearning","NaturalLanguage","Philosophy",\
                 "Reasoning","Representation", "Robots","ScienceFiction",\
                 "Speech", "Systems","Vision"]
        
        
        
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
            print "\n****** Inserting category article word freqs ******\n"
            sql = '''select u.urlid, u.content from cat_corpus as u'''
            rows = self.db.selectall(sql)
            urlids = []
            i = 0
            for row in rows:
                print "%d/%d" % (i, len(rows))
                i += 1
                urlids.append(row[0])
                wordfreq = self.txtpro.simpletextprocess(row[1])
                self.add_freq_index(wordfreq)
            self.commit_freq_index('wordlist')
                
            for category in self.categories:
                self.train_centroid(category, urlids, 'centroid')
        else:
            self.train_centroid(category)
        
    def train_centroid(self, category, corpus, model_dir):
        '''
        Train only one centroid of given category.
        Given the input training data in the src_dir, and output centroid
        saved as pickle file in the dest_dir.
        '''
        print "\n****** Training", category,"******"
        print "(1) Getting articles"
        corp = []
        for c in corpus:
            if category in c[2].split(' '):
                print c[0],
                corp.append(c)
        print
        print "(2) Making centroid"
        centroid = self.make_centroid(corp)
        print "(3) Saving centroid",
        savepickle(paths['ainews.category_data']+model_dir+'/'+category+'.pkl', centroid)
        
    def make_centroid(self, corpus):
        '''
        Build centroid of one category
        '''
        centroid = {} # will hold final centroid avg tfidf, indexed by wordid
        for c in corpus:
            data = self.get_tfidf(c[0], c[1])
            for word in data:
                centroid.setdefault(word, 0.0)
                centroid[word] += data[word]

        distsq = 0.0
        for word in centroid:
            distsq += centroid[word]*centroid[word]

        # Normalize centroid
        dist = math.sqrt(distsq)
        for key in centroid:
            centroid[key] /= dist
            
        return centroid
    
    
    ##############################
    #
    #           Predict 
    #
    ##############################
    def init_predict(self, model_dir = None, wordlist_table = 'wordlist'):
        '''
        Initialization prediction by loading 19 centroids from the directory.
        @param  model_dir: 19 centroid models path dir
        @type  model_dir: C{string}
        '''
        self.models = []
        if model_dir != None:
            for category in self.categories:
                file = os.path.join(model_dir, category+".pkl")
                self.models.append(loadpickle(file))
        self.dftext = {}
        rows = self.db.selectall('select rowid, word, dftext from %s' % wordlist_table)
        for row in rows:
            self.dftext[row[1]] = (row[0], row[2])
            
    def get_tfidf(self, urlid, content = None):
        """
        Helper function to retrieve the tfidf of each word based on the urlid.
        @param  urlid: target news story's urlid.
        @type  urlid: C{int}
        """
        if urlid in self.cache_urls:
            return self.cache_urls[urlid]
            
        wordids = {}
        if content == None:
            sql = '''select w.wordid, t.freq, w.dftext
                     from textwordurl as t, wordlist_eval as w
                     where urlid = %d and t.wordid = w.rowid''' % (urlid)
            rows = self.db.selectall(sql)
            for row in rows:
                # add 1 to dftext since that word is in this doc, too
                words[row[0]] = (row[1], row[2]+1)
        else:
            wordfreq = self.txtpro.simpletextprocess(content)
            for word in wordfreq:
                if word in self.dftext:
                    # add 1 to dftext since that word is in this doc, too
                    wordids[self.dftext[word][0]] = (wordfreq[word], self.dftext[word][1]+1)

        data = {}
        distsq = 0.0
        for word in wordids:
            tfidf = math.log(wordids[word][0], 2) * (math.log(self.corpus_count, 2) - \
                 math.log(wordids[word][1], 2))
            data[word] = tfidf
            distsq += tfidf * tfidf
        dist = math.sqrt(distsq)
        for key in data:
            data[key] /= dist
        self.cache_urls[urlid] = data
        return data
    
    def predict(self, urlid, content = None):
        '''
        Predict its category from the 19 centroids
        Given a urlid of news story, retrieve its saved term vector and
        compare it with 19 category's centroid. Choose the closest category
        as the news story's category/topic.
        '''
        data = self.get_tfidf(urlid, content)
        max_sim = 0
        max_i = 0
        similarities = {}
        for (i, model) in enumerate(self.models):
            sim = self.cos_sim(data, model)
            similarities[self.categories[i]] = sim
            if sim > max_sim:
                max_i = i
                max_sim = sim
        return (self.categories[max_i], similarities)

    def choose_category(self, urlid):
        '''
        Predict and set the article's category.
        '''
        meta = loadpickle(paths['ainews.news_data']+'meta/'+str(urlid)+'.pkl')
        text = loadpickle(paths['ainews.news_data']+'text/'+str(urlid)+'.pkl')
        wordfreq = self.txtpro.simpletextprocess(text)
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

    def cos_sim(self, data, centroid):
        '''
        A helper function to compute the cos simliarity between
        news story and centroid.
        @param  data: target news story tfidf vector.
        @type  data: C{dict}
        @param centroid: centroid tfidf vector.
        @type  centroid: C{dict}
        '''
        numcommon = 0
        sim = 0.0
        for key in data:
            if key in centroid:
                numcommon += 1
                sim += data[key]*centroid[key]
        #print "words common:", numcommon, "data total:", len(data), "centroid total:", len(centroid)
        return sim

    def add_freq_index(self, words):
        for word in words:
            self.wordlist.setdefault(word, 0)
            self.wordlist[word] += 1

    def commit_freq_index(self, table):
        for word in self.wordlist:
            self.db.execute("insert into "+table+" (word, dftext) values(%s, %s)", \
                (word, self.wordlist[word]))
        self.wordlist = {}


    ##############################
    #
    #           Evaluate
    #
    ##############################

    def evaluate(self):
        '''
        Train on a portion of the corpus, and predict the rest;
        evaluate performance. Various parameters are evaluated.
        @param model_dir: temporary directory to store centroids
        @type model_dir: C{string}
        '''
        random.seed()
        results = {} 
        for iteration in range(0, 10):
            for i in range(1, 10):
                pct = i/10.0
                print "Selecting random %d%% of corpus." % (pct * 100)
                rows = list(self.db.selectall( \
                    "select c.urlid, c.content, group_concat(cc.category separator ' ') " +
                    "from cat_corpus as c, cat_corpus_cats_single as cc where c.urlid = cc.urlid " +
                    "group by c.urlid"))
                random.shuffle(rows)
                random.shuffle(rows)
                offset = int(len(rows)*pct)
                self.corpus_count = offset+1
                train_corpus = rows[0:offset]
                # always predict 10%
                predict_corpus = rows[offset:offset+int(len(rows)*0.1)]
    
                self.db.execute("delete from wordlist_eval")
                self.db.execute("alter table wordlist_eval auto_increment = 0")
    
                for c in train_corpus:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                    wordfreq = self.txtpro.simpletextprocess(c[1])
                    self.add_freq_index(wordfreq)
                self.commit_freq_index('wordlist_eval')
                print
    
                # init_predict here to establish self.dftext
                self.init_predict(paths['ainews.category_data']+'centroid_eval/', 'wordlist_eval')
                for category in self.categories:
                    self.train_centroid(category, train_corpus, 'centroid_eval')
                print
                
                # init_predict here to establish newly trained models
                self.init_predict(paths['ainews.category_data']+'centroid_eval/', 'wordlist_eval')
                count_matched = 0
                for c in predict_corpus:
                    (topic, topicsims) = self.predict(c[0], c[1])
                    if topic in c[2].split(' '):
                        sys.stdout.write('+')
                        count_matched += 1
                    else:
                        sys.stdout.write('.')
                    sys.stdout.flush()
                print
                result = 100.0*float(count_matched)/float(len(predict_corpus))
                results.setdefault(i, [])
                results[i].append(result)
                print "Matched: %d/%d = %f%%" % \
                    (count_matched, len(predict_corpus), result)

        print
        print "Summary:"
        for i in results:
            mean, std = meanstdv(results[i])
            print "%d%% matched avg %f%% (std dev %f%%)" % (10*i, mean, std)
            print results[i]
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
        print "Provide 'train' or 'evaluate'"
        sys.exit()
    
    if sys.argv[1] == "train":
        cat.train()
    elif sys.argv[1] == "evaluate":
        cat.evaluate()
        
    print "\n\n"
    print datetime.now() - start   
       
        
     
