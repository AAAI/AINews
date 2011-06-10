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
import math
from subprocess import *
import time
from datetime import datetime

from AINewsDB import AINewsDB
from AINewsTextProcessor import AINewsTextProcessor
from AINewsTools import loadfile2, savefile, savepickle, loadpickle, loadfile
from AINewsConfig import config


class AINewsCentroidClassifier:
    def __init__(self):
        '''
        Initialization of centroid classifier for 19 AI-topic 
        '''
        self.txtpro = AINewsTextProcessor()
        self.db = AINewsDB()
        total_doc = self.db.get_totaldoc()
        self.logN = math.log(total_doc+1,2)
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
    def train(self, src_dir, dest_dir, category=None):
        '''
        Training procedures for all 19 centroids 
        It takes in 19 topics' training data from the src_dir,
        and outputs centroid of each topic into dest_dir.
        If category is not None, then only train that specific category.
        '''
        if category == None:
            for category in self.categories:
                self.train_centroid(src_dir, dest_dir, category)
        else:
            self.train_centroid(src_dir,dest_dir, category)
        
    def train_centroid(self, src_dir, dest_dir, category):
        '''
        Train only one centroid of given category.
        Given the input training data in the src_dir, and output centroid
        saved as pickle file in the dest_dir.
        '''
        print "\n****** Training", category,"******"
        print "(1) Extracting words from training data"
        src = os.path.join(src_dir, category)
        allw, artw, artt = self.getarticlewords(src)
        
        print "(2) Making centroid"
        centroid = self.make_centroid(allw, artw, float(len(artt)))
        print "(3) Save centroid",
        dest_file = os.path.join(dest_dir,category+".pkl")
        print dest_file
        savepickle(dest_file, centroid)
        
    def train_data_generator(self, src_dir):
        '''
        Python Generator to browse all the training files under given directory.
        '''
        files = sorted([f for f in os.listdir(src_dir) 
                if os.path.isfile(os.path.join(src_dir, f)) ])
        for file in files:
            yield file
                
    def getarticlewords(self, src_dir):
        '''
        Process all the words from the training corpus. Codes are referred from 
        book 'collective intelligence' chapter 10.
        '''
        allwords={}
        articlewords=[]
        articletitles=[]
        cnt = 0
        
        train_data = self.train_data_generator(src_dir)
        for file_data in train_data:
            file = os.path.join(src_dir, file_data)
            title = file_data.encode('utf8')
            
            # Extract the words
            content = loadfile2(file)
            text = title + ' ' + content
            wordfreq = self.txtpro.simpletextprocess(text)
            articlewords.append({})
            articletitles.append(title)
            # Increase the counts for this word in allwords 
            for word in wordfreq.keys():
                allwords.setdefault(word,0)
                allwords[word] += 1
                articlewords[cnt][word] = wordfreq[word]
            cnt += 1
            
        return allwords,articlewords,articletitles
    
    def make_centroid(self, allw, articlew, N):
        '''
        Build centroid of one category
        '''
        wordmap = {}    # Mapping word->AINewsDB's wordlist (id, log(N/df))

        # Build IDF for all words
        for w,c in allw.items():
            sql = "select rowid, dftext from wordlist where word = '%s'" % w
            row = self.db.selectone(sql)
            if row == None: continue
            wordmap[w] = (row[0], (self.logN - math.log(row[1]+1, 2)))
                
        # Compute Centroid of classifier (Added by Liang Dong)
        centroid = {}
        for f in articlew:
            curr = {}
            distsq = 0.0
            
            # compute tf*idf
            for word in f.keys():
                if word in wordmap.keys():
                    tfidf =  math.log(f[word]+1,2)*wordmap[word][1]
                    curr[wordmap[word][0]] = tfidf
                    distsq += tfidf * tfidf
            
            # add normalized doc to centroid
            dist = math.sqrt(distsq)
            for key in curr.keys():        
                centroid.setdefault(key, 0)
                centroid[key] += curr[key]/dist
                
                
        # Average to get centroid
        distsq = 0.0
        for key in centroid.keys():
            val = centroid[key]/N
            centroid[key] = val
            distsq += val * val
        # Normalize centroid
        dist = math.sqrt(distsq)
        for key in centroid.keys():
            centroid[key] /= dist
            
        return centroid
    
    
    
    
    
    
    ##############################
    #
    #           Predict 
    #
    ##############################
    def init_predict(self, model_dir):
        '''
        Initialization prediction by loading 19 centroids from the directory.
        @param  model_dir: 19 centroid models path dir
        @type  model_dir: C{string}
        '''
        
        self.models = []
        
        print "Loading Centroid Classifier"
        for category in self.categories:
            file = os.path.join(model_dir, category+".pkl")
            self.models.append(loadpickle(file))
        
        self.cache_urls = {}
   
            
    def get_tfidf(self, urlid):
        """
        Helper function to retrieve the tfidf of each word based on the urlid.
        @param  urlid: target news story's urlid.
        @type  urlid: C{int}
        """
        if urlid in self.cache_urls.keys():
            return self.cache_urls[urlid]
            
        sql = '''select t.wordid, t.freq, w.dftext
                 from textwordurl as t, wordlist as w
                 where urlid = %d and t.wordid = w.rowid''' % (urlid)
        rows = self.db.selectall(sql)
        data = {}
        distsq = 0.0
        for row in rows:
            tfidf = (math.log(row[1]+1, 2)) * (self.logN-math.log(row[2]+1,2))
            data[row[0]] = tfidf
            distsq += tfidf * tfidf
        dist = math.sqrt(distsq)
        for key in data.keys():
            data[key] /= dist
        self.cache_urls[urlid] = data
        return data
    
    def predict(self, urlid, debug = False):
        '''
        Predict its category from the 19 centroids
        Given a urlid of news story, retrieve its saved term vector and
        compare it with 19 category's centroid. Choose the closest category
        as the news story's category/topic.
        '''
        data = self.get_tfidf(urlid)
        max_sim = 0
        max_i = 0
        for (i, model) in enumerate(self.models):
            sim = self.cos_sim(data, model)
            #print '\t', self.categories[i], sim
            if sim > max_sim:
                max_i = i
                max_sim = sim
        if debug: print urlid, self.categories[max_i], max_sim
        return self.categories[max_i]
        
    def cos_sim(self, data, centroid):
        '''
        A helper function to compute the cos simliarity between
        news story and centroid.
        @param  data: target news story tfidf vector.
        @type  data: C{dict}
        @param centroid: centroid tfidf vector.
        @type  centroid: C{dict}
        '''
        sim = 0.0
        for key in data.keys():
            if key in centroid.keys():
                sim += data[key]*centroid[key]
        return sim
        
        
if __name__ == "__main__":
    start = datetime.now()
    
    cat = AINewsCentroidClassifier()
    
    TRAIN, PREDICT = range(0,2)
    
    type =  PREDICT
    
    if type == TRAIN:
        src_dir = "category/smalldata/"
        dest_dir = "category/centroid/"
        cat.train(src_dir, dest_dir)
        
    elif type == PREDICT:
        model_dir = "category/centroid/"
        cat.init_predict(model_dir)
        for urlid in range(650,675):
            cat.predict(urlid, debug = True)
        
    print datetime.now() - start   
       
        
     
