"""
AINewsSVMClassifier aims to use SVM to train and predict 19 AI news categories.

The classification task was performed by AINewsTopic.py, but it is a rather
simply method.

I crawled 1281 documents using LuceneCategoryCrawler.py from 19 categories from
AITopic (http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/HomePage)

Date: Dec.19th, 2010
Author: Liang Dong
"""

import os
import math
from svm import *
from subprocess import *
import time
from datetime import datetime

from AINewsDB import AINewsDB
from AINewsTextProcessor import AINewsTextProcessor
from AINewsTools import loadfile2, savefile, savepickle, loadpickle, loadfile
from AINewsConfig import config


class AINewsSVMClassifier:
    def __init__(self):
        self.txtpro = AINewsTextProcessor()
        self.db = AINewsDB()
        total_doc = self.db.get_totaldoc()
        self.logN = math.log(total_doc+1,2)
        self.upper_df = total_doc * float(config['svm.docfreq_upper_ratio'])
        self.lower_df = total_doc * float(config['svm.docfreq_lower_ratio'])
        #self.categories = loadpickle("category/all_categories.pkl")
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
    def train(self, src_dir, dest_dir):
        
        print "(1) Extracting words from training data"
        allw, artw, artt, artcat, allcat = self.getarticlewords(src_dir)
        #self.categories = sorted(list(allcat))
        #savepickle("category/all_categories.pkl", self.categories)
        
        print "(2) Computing TFIDF and base libsvm format"
        formats, wordmap = self.make_libsvm_input(allw, artw)
        
        print len(formats), len(artcat), len(allcat)
        
        print "(3) Building LibSVM training input format"
        for category in self.categories:
            content = ""
            for (i,artcategory) in enumerate(artcat):
                if category == artcategory:
                    content += "+1   "+formats[i]+'\n'
                else:
                    content += "-1   "+formats[i]+'\n'
            target_file = os.path.join(dest_dir, category+"_train")
            savefile(target_file, content)
        
        
        print "(4) Training 1-against-rest classifier for each category"
        
        for category in self.categories:
            print "\tTraining ", category
            start = datetime.now()
            filename = os.path.join(paths['ainews.category_data'], dest_dir, category+"_train")
            cmd = 'python svm-easy.py "%s" ' % filename
            Popen(cmd, shell = True, stdout = PIPE).communicate()
            end = datetime.now()
            print "\tTime spent:", end - start
        
        print "(5) Done"
        
        
    def train_data_generator(self, src_dir):
        '''
        Python Generator to browse all the training files under given directory.
        '''
        dirs = sorted([f for f in os.listdir(src_dir) 
                if os.path.isdir(os.path.join(src_dir, f)) ])
        for dir in dirs:
            files = sorted([f for f in os.listdir(os.path.join(src_dir,dir))])
            for file in files:
                yield (dir, file)
                
    def getarticlewords(self, src_dir):
        '''
        Process all the words from the training corpus. Codes are referred from 
        book 'collective intelligence' chapter 10.
        '''
        allwords={}
        articlewords=[]
        articletitles=[]
        articlecategories = []
        allcategories = set()
        cnt = 0
        
        train_data = self.train_data_generator(src_dir)
        for file_data in train_data:
            file = os.path.join(src_dir, file_data[0], file_data[1])
            title = file_data[1].encode('utf8')
            
            # Extract the words
            content = loadfile2(file)
            text = title + ' ' + content
            wordfreq = self.txtpro.simpletextprocess(text)
            articlewords.append({})
            articletitles.append(title)
            articlecategories.append(file_data[0])
            allcategories.add(file_data[0])
            
            # Increase the counts for this word in allwords 
            for word in wordfreq.keys():
                allwords.setdefault(word,0)
                allwords[word] += 1
                articlewords[cnt][word] = wordfreq[word]
            cnt += 1
            
        return allwords,articlewords,articletitles, articlecategories, allcategories
    
    def make_libsvm_input(self, allw, articlew):
        '''
        Build the base libsvm input format for all the articles.
        '''
        
        wordmap = {}    # Mapping word->AINewsDB's wordlist (id, log(N/df))

        # Only take words that are common but not too common
        # From allwords
        N = len(articlew)
        upper = N * 0.6
        lower = 3
        for w,c in allw.items():
            if c > lower and c < upper:
                sql = "select rowid, dftext from wordlist where word = '%s'" % w
                row = self.db.selectone(sql)
                if row == None:
                    # print '\'',w, "\' not found"
                    continue
                wordmap[w] = (row[0], (self.logN - math.log(row[1]+1, 2)))
                
                
        # Create the libsvm input 
        # TFIDF the value (Added by Liang Dong)
        l1 = []
        cnt = 0
        for f in articlew:
            l1.append({})
            for word in f.keys():
                if word in wordmap.keys():
                    l1[cnt][wordmap[word][0]] = math.log(f[word]+1,2)*wordmap[word][1]
            cnt += 1
            
        baseformats = []
        for item in l1:
            text = ""
            for wordid in sorted(item.keys()):
                text += str(wordid)+":"+str(item[wordid])+" "
            baseformats.append(text)
            
        return baseformats, wordmap
    
    ##############################
    #
    #           Predict 
    #
    ##############################
    def init_predict(self, model_dir):
        self.allwords_idf = {}
        self.build_allwords_idf()
        self.models = []
        
        for category in self.categories:
            file = os.path.join(model_dir, category+"_train.model")
            print "Loading SVM model:", file
            self.models.append(svm_model(file))
        
        self.range = {}
        rangefile = os.path.join(model_dir, "AIOverview_train.range")
        self.__load_range(rangefile)
    
    def build_allwords_idf(self):
        """
        Pre-calculate the idf value for all the words whose doc freq value
        belongs to the certain range (lower_df, upper_df).
        """
        sql = '''select rowid, dftext from wordlist
                 where dftext > %d and dftext < %d
              ''' % (self.lower_df, self.upper_df)
        rows = self.db.selectall(sql)
        for row in rows:
            idf = self.logN - math.log(row[1]+1, 2)
            self.allwords_idf[row[0]] = idf
            
    def __load_range(self, filename):
        """
        Read in the range file generated by svm-train tool which list the min
        and max value of each feature. Since the min value is always 0, only
        the max value is read and stored in a dictionary
        self.range[wordid] = max_value of the feature
        @param filename: the libSVM formatted input file
        @type filename: C{string}
        """
        lines = loadfile(filename)
        for line in lines[2:]:
            items = line[:-1].split(' ')
            self.range[int(items[0])] = float(items[2]) 
    
    def __retrieve_url_tfidf(self, urlid):
        """
        Retrieve the tfidf of each word based on the urlid.
        @param  urlid: target news story's urlid.
        @type  urlid: C{int}
        """
        sql = '''select t.wordid,t.freq from textwordurl as t, wordlist as w
                    where urlid = %d and t.wordid = w.rowid and dftext > %d
                    and dftext < %d''' % (urlid, self.lower_df, self.upper_df)
        rows = self.db.selectall(sql)
        data = {}
        for row in rows:
            if row[0] not in self.range.keys():
                continue
            tfidf = (math.log(row[1]+1, 2)) * self.allwords_idf[row[0]]
            data[row[0]] = tfidf / self.range[row[0]]
        return data
    
    def predict(self, urlid):
        data = self.__retrieve_url_tfidf(urlid)
        max_prob = 0
        max_i = 0
        for (i, model) in enumerate(self.models):
            prob = model.predict_probability(data)
            print self.categories[i], prob
            if prob[1][1] > max_prob:
                max_i = i
                max_prob = prob[1][1]
        print urlid, self.categories[max_i], max_prob
        
if __name__ == "__main__":
    start = datetime.now()
    
    cat = AINewsSVMClassifier()
    
    VIEW_ALL_FILE, TRAIN, PREDICT = range(0,3)
    
    type =  PREDICT
    
    if type == VIEW_ALL_FILE:
        src_dir = "category/data"
        dirs = sorted([f for f in os.listdir(src_dir) 
                    if os.path.isdir(os.path.join(src_dir, f)) ])
        cnt = 0
        for dir in dirs:
            files = sorted([f for f in os.listdir(os.path.join(src_dir,dir))])
            for (i,file) in enumerate(files):
                print cnt, i, dir, file
                cnt += 1
                
    elif type == TRAIN:
        src_dir = "category/newdata"
        dest_dir = "category/newmodels"
        cat.train(src_dir, dest_dir)
        
    elif type == PREDICT:
        model_dir = "category/newmodels"
        cat.init_predict(model_dir)
        for urlid in range(650,675):
            cat.predict(urlid)
        
        
    print datetime.now() - start    
        
       
        
     
