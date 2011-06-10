"""
AINewsSVM utilizes the libSVM library to train the news's AI related rating.
It collects all the user's rating as training dataset from the path:
pmwiki/pub/rater/logs/. For each news story, the tfidf is measured and
trained into three categories(0,+1),(+2,+3),(+4,+5).
"""

import math
import glob
import stat
from os import chdir,getcwd,path,chmod
from svmutil import *
from subprocess import *

from AINewsConfig import config
from AINewsTools import loadcsv, savefile, loadfile
from AINewsDB import AINewsDB

class AINewsSVM:
    def __init__(self):
        """
        Initialize the parameters of AINewsSVM
        """
        self.db = AINewsDB()
        self.debug = config['ainews.debug']
       
        self.entries = {}
        self.scores = {}               # store pair (urlid -> user's rating)
        self.allnews = {}
        self.allwords_idf = {}
        self.range = {}
        
        res = self.db.selectone('select count(*) from urllist')
        self.total_N = res[0]
        self.logN = math.log(self.total_N + 1, 2)
        self.upper_df = self.total_N * float(config['svm.docfreq_upper_ratio'])
        self.lower_df = self.total_N * float(config['svm.docfreq_lower_ratio'])
        self.build_allwords_idf()
        
    ####################################################################
    #
    #           SVM Initialization
    #        Called from outside (AINews.py)
    #   Train:  collect_feedback() load_news_words() train_all() in AINews.py
    #   Prediction: load_news_words() in AINewsRanker.py
    #   
    ###################################################################      
    def collect_feedback(self):
        """
        Collect user's feedback and generate an output file with mean, st.dev.
        """
        feedback_path = config['pmwiki.dir'] + 'pub/rater/logs/'
        rater_count_cutoff = int(config['feedback.rater_count_cutoff'])
        stdev_cutoff  = float(config['feedback.stdev_cutoff'])
        output = ""
        #admins = ("Bgbuchanan's", "Rgsmith's", "Ldong's")
        admins = [name + '\'s' for name in config['svm.admins'].split(':')]
        for infile in glob.glob( path.join(feedback_path, '*.rating') ):
            urlid = int(infile.split('/')[-1][:-7])
            lines = loadfile(infile)
            n = len(lines)
            newsscore = -1
            
            # Measuring standard deviation and mean. Save them into database.
            rates = []
            for line in lines:
                rates.append(int(line.split('|')[0]))
            mean = sum(rates) * 1.0 / n
            sd = math.sqrt(sum((x - mean)**2 for x in rates) / n)
            sql = "UPDATE urllist SET rate = %f, ratesd = %f, ratecount = %d \
                    WHERE rowid = %d" \
                    % (float(mean), float(sd), n,  urlid )
            self.db.execute(sql)
            
            if False:
                # Deprecated. Dr.Buchanan wants only his and Dr.Reids' rating
                # be used in re-training
                if n <= rater_count_cutoff: continue
                rates = []
                for line in lines:
                    rates.append(int(line.split('|')[0]))
                mean = sum(rates) * 1.0 / n
                sd = math.sqrt(sum((x - mean)**2 for x in rates) / n)
                if sd > stdev_cutoff: continue
                newsscore = mean
            else:
                # Only use Dr.Buchanan and Dr.Reids' rating for re-training
                admincount = 0
                adminsum = 0
                for line in lines:
                    items = line.split('|')
                    if items[2].rstrip() in admins:
                        adminsum += int(items[0])
                        admincount += 1
                if admincount != 0:
                    adminavg = 1.0 * adminsum / admincount
                    newsscore = adminavg
                    sql = "UPDATE urllist SET adminrate = %f WHERE rowid = %d"\
                            % (float(adminavg), urlid )
                    self.db.execute(sql)
                        
            if newsscore == -1: 
                #if n <= rater_count_cutoff: continue
                if sd > stdev_cutoff: continue
                newsscore = mean
            self.scores[urlid] = float(newsscore)
            output += "%d:%f:%f:%d\n" % (urlid, newsscore, sd, n)
            
            
        savefile(config['feedback.feedback_score'], output)
        
        
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
    
    def load_news_words(self):
        """
        Called in AINewsRanker
        For each url/news, measure the tfidf of each word.
        """
        for urlid in self.scores.keys():
            if urlid in self.allnews.keys(): continue
            
            sql = '''select t.wordid,t.freq from textwordurl as t, wordlist as w
                    where urlid = %d and t.wordid = w.rowid and dftext > %d
                    and dftext < %d''' % (urlid, self.lower_df, self.upper_df)
            rows = self.db.selectall(sql)
            
            doc = {}
            for row in rows:
                doc[row[0]] = (math.log(row[1] + 1, 2)) * \
                                self.allwords_idf[row[0]]
                
            self.allnews[urlid] = doc
        '''        
        self.matrix=[[(wordid in self.allnews[urlid].keys() \
                        and self.allnews[urlid][wordid] or 0) \
                            for wordid in self.allwords_idf.keys()] \
                        for urlid in self.allnews.keys()]
        '''
        
    def get_tfidf(self, urlid):
        """
        Given a news urlid, compute its tfidf and save into cache.
        """
        if urlid in self.allnews.keys():
            return self.allnews[urlid]
        else:
            sql = '''select t.wordid,t.freq from textwordurl as t, wordlist as w
                    where urlid = %d and t.wordid = w.rowid and dftext > %d
                    and dftext < %d''' % (urlid, self.lower_df, self.upper_df)
            rows = self.db.selectall(sql)
            
            doc = {}
            for row in rows:
                doc[row[0]] = (math.log(row[1] + 1, 2)) * \
                                self.allwords_idf[row[0]]
                
            self.allnews[urlid] = doc
            return doc
            
        
    ###########################################
    #
    #           SVM Training
    #
    ###########################################       
    
    def train(self, filename, pos_range):
        """
        Using libSVM to train the training dataset based on the positive range, 
        and save the training result into the filename.
        @param filename: the libSVM formatted input file's name without suffix.
        @type filename: C{string}
        @param pos_range: The +1 positive range [a,b]
        @type pos_range: C{tuple}
        """
        # Generate the specific input format file
        self.__generate_libsvm_input(pos_range,  filename)
        # Using the input file to train SVM
        self.__libsvm_train(filename)
        
    def train_all(self):
        """
        The three categories SVM trainer.
        """
        self.train("45", (3.33, 5.01))
        self.train("23", (1.67, 3.33))
        self.train("01", (0, 1.67))
    
    def __generate_libsvm_input(self, pos, filename):
        """
        Generate the input file based on libSVM's input format.
        @param filename: the libSVM formatted input file's name without suffix.
        @type filename: C{string}
        @param pos: The +1 positive range [a,b]
        @type pos: C{tuple}
        """
        content = ""
        for urlid in self.scores.keys():
            score = self.scores[urlid]
            if score >= pos[0] and score < pos[1]: line = "+1  "
            else: line = "-1  "
            
            for wordid in sorted(self.allnews[urlid].keys()):
                line += ' '+str(wordid)+':'+str(self.allnews[urlid][wordid])
            content += line + '\n'
        savefile('svm/'+filename, content)
    
    def __libsvm_train(self,filename):
        """
        Use system call LIBSVM_TOOL from bash shell to train SVM model. The
        easy.py python file is an automatic executive file for all the training 
        process which is from the libSVM's library pack.
        @param filename: the libSVM formatted input file
        @type filename: C{string}
        """
        cwd = getcwd()
        svm_path = config['ainews.ainews_root'] + 'svm'
        chdir(svm_path)
        cmd = 'python easy.py "%s"' % filename
        Popen(cmd, shell = True, stdout = PIPE).communicate()
        chdir(cwd)
            
      
    
        
    ###########################################
    #
    #            SVM Prediction
    #
    ###########################################
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
            # self.range is used in __retrieve_url_tfidf()
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

    
    def predict_probability(self, filename, urlids):
        """
        Load the trained SVM and for each latest crawled news stories, predict
        the categories it belongs to. It gets the probability which it belongs
        to certain category.
        @param filename: the libSVM formatted input file's name without suffix
        @type filename: C{string}
        @param urlids: list of latest news' urlid to be predicted
        @type urlids: C{list}
        """
        svm_path = config['ainews.ainews_root']+"svm/"
        mysvm = svm_load_model(svm_path + filename + ".model")
        self.__load_range(svm_path + filename + ".range")
        results = []
        for urlid in urlids:
            data = self.__retrieve_url_tfidf(urlid)
            p = svm_predict([0], [data], mysvm, "-b 1")
            # p = ([1.0], _, [[0.62317989329642587 0.3768201067035743]])
            # where the first prob is for -1, the second for 1
            results.append(p[2][0][1])
        return results
    
        
    def predict_probability_all(self, urlids):
        """
        Use the three categories SVM trainer to predict probability of latest
        news stores.
        @param urlids: list of latest news' urlid to be predicted
        @type urlids: C{list}
        """

        predicts_45 = self.predict_probability("45", urlids)
        predicts_23 = self.predict_probability("23", urlids)
        predicts_01 = self.predict_probability("01", urlids)
        return zip(urlids, predicts_45, predicts_23, predicts_01)
        
    def predict(self, filename, urlids):
        """
        Load the trained SVM and for each latest crawled news stories, predict
        the categories it belongs to. The belonging category receives +1,
        otherwise -1.
        @param filename: the libSVM formatted input file's name without suffix
        @type filename: C{string}
        @param urlids: list of latest news' urlid to be predicted
        @type urlids: C{list}
        """
        svm_path = config['ainews.ainews_root']+"svm/"
        mysvm = svm_load_model(svm_path + filename + ".model")
        self.__load_range(svm_path + filename + ".range")
        results = []
        for urlid in urlids:
            data = self.__retrieve_url_tfidf(urlid)
            cat = svm_predict([0], [data], mysvm)
            print cat
            results.append(cat)
        return results
    
    def predict_all(self, urlids):
        """
        Use the three categories SVM trainer to predict the latest news stores.
        @param urlids: list of latest news' urlid to be predicted
        @type urlids: C{list}
        """
        predicts_45 = self.predict("45", urlids)
        predicts_23 = self.predict("23", urlids)
        predicts_01 = self.predict("01", urlids)
        return zip(urlids, predicts_45, predicts_23, predicts_01)

    
    ###########################################
    #
    #  Train Related/NotRelated Classifier
    #
    ##########################################
    def train_isrelated(self):
        '''
        It trains the SVM classifier to classify AI-related or AI-NotRelated
        news to screen those news containing AI-Whitelist terms but is not
        actually discussing about AI.
        '''
        ## The "NotRelated" classification comes from crawl()
        ## in AINewsCrawler; this model (svm/IsRelated)
        ## is updated when training is called from AINews
        ## or when AINewsSVM is run directly

        # Generate libsvm input file
        content = ""
        ## Early URLs (before 314) have no 'description' field values
        for urlid in range(314, self.total_N):
            topic = self.get_related(urlid)
            if topic == None: continue
            if topic == "NotRelated": line = "-1  "
            else: line = "+1  "

            doc = self.get_tfidf(urlid)
            for wordid in sorted(doc.keys()):
                line += ' '+str(wordid)+':'+str(doc[wordid])
            content += line + '\n'
        savefile('svm/IsRelated', content)
        
        # use libsvm command tool to train
        cwd = getcwd()
        svm_path = config['ainews.ainews_root'] + 'svm'
        chdir(svm_path)
        cmd = 'python easy.py IsRelated'
        Popen(cmd, shell = True, stdout = PIPE).communicate()
        chdir(cwd)
            
    def get_related(self, urlid):
        sql = "select topic from urllist where rowid = %d" % urlid
        row = self.db.selectone(sql)
        if row == None: return None
        return row[0]
    ###########################################
    #
    #    Following codes below are deprecated    
    #
    ###########################################
        
    # Dr.Buchanan said we don't need that complicated, thus this function
    # is not called any more.
    def train_parameter(self):
        """
        After the classifiers are trained, we use the classifier to test the
        training data and get the SVM score via u*prob(45) + v*prob(23) +
        (1-u-v)*prob(01). We get the u,v's value via compute the correlation
        with user's rating.
        
        Given a dataset of user rate, use predict_probability to predict
        the user rate and compute the correlation of the user rate. To maximize
        the correlation, we compute the parameter u, v where
        predict_rate = u*prob(45) + v*prob(23) + (1-u-v)*prob(01)
        After computing u,v, values are stored in file "svm/coefficient.txt".
        """
        predicts_45 = self.predict_probability("45", self.scores.keys())
        predicts_23 = self.predict_probability("23", self.scores.keys())
        predicts_01 = self.predict_probability("01", self.scores.keys())
        
        y = self.scores.values()
        rate_mean, rate_var = MeanAndVar(y)
        pre45_mean, pre45_var = MeanAndVar(predicts_45)
        pre23_mean, pre23_var = MeanAndVar(predicts_23)
        pre01_mean, pre01_var = MeanAndVar(predicts_01)
        
        maxu = maxv = maxcor=0
        for uu in range(50, 101, 10):
            for vv in range(0, 101-uu, 10):
                u = uu/100.0
                v = vv/100.0
                x = [(u*predicts_45[i]+v*predicts_23[i]+\
                          (1-u-v)*predicts_01[i]) for i in range(len(y))]
                x_mean, x_var = MeanAndVar(x)
                sumsqr = sum([x[i]*y[i] for i in range(len(y))])
                correlation = (1.0*sumsqr/len(y) - x_mean*rate_mean)/(math.sqrt(x_var*rate_var))
                #testcor = Correlation(x,y)
                #print u, v, '\t',correlation, testcor
                if correlation > maxcor:
                    maxu=u
                    maxv=v
                    maxcor = correlation
        savefile("svm/coefficient.txt", str(maxu)+' '+str(maxv)+' '+str(maxcor))
        #print "max", maxu,maxv,maxcor
        
    def print_entries(self):
        """
        Print out the TFIDF for each urlid.
        """
        for urlid in self.entries.keys():
            print urlid, self.entries[urlid]
 

def MeanAndVar(arr):
    mean = 1.0 * sum(arr) / len(arr)
    var = 1.0 * sum([i*i for i in arr]) / len(arr) - mean*mean
    return (mean, var)

def Correlation(x, y):
    assert(len(x) == len(y))
    assert(len(x) > 0)
    meanx, varx = MeanAndVar(x)
    meany, vary = MeanAndVar(y)
    sumsqr = sum([x[i]*y[i] for i in range(len(x))])
    return (1.0*sumsqr/len(x) - meanx*meany)/(math.sqrt(varx*vary))
    

    
    
        
    '''
    def build_training_data(self):
        """
        Deprecated.
        
        Load the training file which lists (human score, id, url, title).
        This training file (default resource/training_score.csv) is edited 
        by admin to manully add human's rating for certain news story.
        The function is used to crawl these news stories which are manuelly 
        rated and haven't been crawled yet.
        """
        from AINewsCrawler import AINewsCrawler
        crawler = AINewsCrawler()
        
        feedback_path = config['pmwiki.dir'] + 'pub/rater/logs/'
        admin_votes = int(config['feedback.admin_votes'])
        # default path: resource/training_score.csv file
        filename = config['svm.training_score_file']
        rows = loadcsv(filename)
        for row in rows:
            if len(row) < 4: continue
            url = row[2]
            if not self.db.isindexed(url):
                crawler.crawl_url(url)
            urlid = self.db.geturlid(url)
            if urlid == -1: continue
            self.entries[urlid]=({'score':int(row[0]),'id':row[1],\
                                  'url':row[2],'title':row[3]})
                                 
            votelogs = "%d|%s|%s\n" % (int(row[0]), "127.0.0.1", "AINews")
            log_file = feedback_path+str(urlid)+".rating"
            
            saveflag = True
            if path.exists(log_file):
                logs = loadfile(log_file)
                for log in logs:
                    if log.split("|")[-1] == "AINews":
                        saveflag = False
                        break
            if saveflag:
                savefile(log_file, votelogs * admin_votes)
                chmod(log_file, 0664)
                #chown(log_file, 'www-data', 'www-data')
            
        output = ""
        for urlid in self.entries.keys():
            e = self.entries[urlid]
            output += ','.join([str(e['score']),str(urlid), '\"' + \
                            e['url'] + '\"','\"' + e['title'] + '\"']) + '\n'
        savefile(filename, output)        
    '''
    
if __name__ == "__main__":
    svm = AINewsSVM()
    svm.train_isrelated()
 
