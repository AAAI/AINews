# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

import sys
import re
from datetime import datetime
from subprocess import *
from svmutil import *
from AINewsConfig import paths
from AINewsCorpus import AINewsCorpus
from AINewsTools import loadfile, savepickle

class AINewsSVMClassifier:
    def __init__(self, testing = False):
        self.corpus = AINewsCorpus(testing)

    def predict(self, articles):
        urlids = sorted(articles.keys())
        for urlid in articles:
            articles[urlid]['categories'] = []

        # produce the test input file
        f = open(paths['svm.svm_data']+'predict', 'w')
        for urlid in urlids:
            for cat in self.corpus.categories:
                articles[urlid]['cat_probs'] = {}
            tfidf = self.corpus.get_tfidf(urlid, articles[urlid]['wordfreq'])
            f.write("+1 ")
            for wordid in sorted(tfidf.keys()):
                f.write("%s:%f " % (wordid, tfidf[wordid]))
            f.write("\n")
        f.close()

        # predict each category plus NotRelated
        for cat in self.corpus.categories:
            cmd = 'svm-scale -r "%s" "%s" > "%s"' % \
                (paths['svm.svm_data']+cat+'.range', \
                paths['svm.svm_data']+'predict', \
                paths['svm.svm_data']+'predict-'+cat+'.scaled')
            Popen(cmd, shell = True).wait()
            cmd = 'svm-predict -b 1 "%s" "%s" "%s" > /dev/null' % \
                (paths['svm.svm_data']+'predict-'+cat+'.scaled', \
                paths['svm.svm_data']+cat+'.model',
                paths['svm.svm_data']+'predict-'+cat+'.output')
            Popen(cmd, shell = True).wait()
            f = open(paths['svm.svm_data']+'predict-'+cat+'.output', 'r')
            lines = f.readlines()
            f.close()
            # first line of output file says "labels -1 1" or whatever;
            # the order could be different, so we have to check
            labels = re.match('labels (-?1) (-?1)', lines[0]).group(1,2)
            if labels[0] == '1': pos_label = 0
            else: pos_label = 1
            for i in range(1, len(lines)):
                (prediction, prob1, prob2) = \
                        re.match('(-?1) (\d\.?\d*e?-?\d*) (\d\.?\d*e?-?\d*)', lines[i]).group(1,2,3)
                if pos_label == 0: prob_yes = prob1
                else: prob_yes = prob2
                articles[urlids[i-1]]['cat_probs'][cat] = prob_yes
                if prediction == '1':
                    articles[urlids[i-1]]['categories'].append(cat)

            for urlid in urlids:
                articles[urlid]['categories'] = sorted(articles[urlid]['categories'])

    def train(self, ident):
        (train_corpus, _) = self.corpus.load_corpus(ident, 1.0, True)
        self.generate_libsvm_input(train_corpus, 'train')
        print "Done generating SVM input."
        self.libsvm_train(False)

    def evaluate(self, ident, pct):
        for i in range(1):
            results = {}
            (train_corpus, predict_corpus) = self.corpus.load_corpus(ident, float(pct), True, True)
            savepickle(paths['svm.svm_data_tmp']+'wordids.pkl', self.corpus.wordids)
            self.generate_libsvm_input(train_corpus, 'train')
            self.generate_libsvm_input(predict_corpus, 'predict')
            print "Done generating SVM input."
            results = self.libsvm_train(True)
            print "Iteration", i, ", pct", pct
            print results
                                                                                                  
    def generate_libsvm_input(self, corpus, suffix):
        train_labels = {}
        train_samples = {}
        for cat in self.corpus.categories:
            train_labels[cat] = []
            train_samples[cat] = []
        for c in corpus:
            cats = c[2].split(' ')
            for cat in self.corpus.categories:
                train_samples[cat].append(self.corpus.get_tfidf(c[0], c[1]))
                if cat in cats:
                    train_labels[cat].append("+1")
                else:
                    train_labels[cat].append("-1")

        for cat in self.corpus.categories:
            # do feature selection
            whole_fsc_dict,whole_imp_v = cal_feat_imp(train_labels[cat], train_samples[cat])
            # choose top 9000 features
            fv = whole_imp_v[:9000]
            tr_sel_samp = select(train_samples[cat], fv)

            model = open(paths['svm.svm_data_tmp']+cat+'-'+suffix, 'w')
            for i in range(len(train_samples[cat])):
                model.write("%s " % train_labels[cat][i])
                for wordid in sorted(tr_sel_samp[i].iterkeys()):
                    model.write("%s:%f " % (wordid, tr_sel_samp[i][wordid]))
                model.write("\n")
            model.close()

    def libsvm_train(self, alsotest):
        results = {}
        # train each category plus NotRelated
        for cat in self.corpus.categories:
            if alsotest:
                sys.stdout.write("Training and testing " + cat + "... ")
            else:
                sys.stdout.write("Training " + cat + "... ")
            sys.stdout.flush()
            if alsotest:
                cmd = 'python svm-easy.py "%s" "%s"' % \
                    (paths['svm.svm_data_tmp']+cat+'-train',
                     paths['svm.svm_data_tmp']+cat+'-predict')
            else:
                cmd = 'python svm-easy.py "%s"' % (paths['svm.svm_data_tmp']+cat+'-train')
            (stdout, _) = Popen(cmd, shell = True, stdout=PIPE).communicate()
            if alsotest:
                m = re.match('.*Accuracy = (\d+).*', re.sub('\n', '', stdout))
                results[cat] = float(m.group(1))
                sys.stdout.write(str(results[cat]) + "\n")
                sys.stdout.flush()
        return results

### from fselect.py
### select features and return new data
def select(sample, feat_v):
	new_samp = []

	feat_v.sort()

	#for each sample
	for s in sample:
		point={}
		#for each feature to select
		for f in feat_v:
			if f in s: point[f]=s[f]

		new_samp.append(point)

	return new_samp

### from fselect.py
### compare function used in list.sort(): sort by element[1]
#def value_cmpf(x,y):
#	if x[1]>y[1]: return -1
#	if x[1]<y[1]: return 1
#	return 0
def value_cmpf(x):
	return (-x[1]);

### from fselect.py
### cal importance of features
### return fscore_dict and feat with desc order
def cal_feat_imp(labels,samples):
	score_dict=cal_Fscore(labels,samples)

	score_tuples = list(score_dict.items())
	score_tuples.sort(key = value_cmpf)

	feat_v = score_tuples
	for i in range(len(feat_v)): feat_v[i]=score_tuples[i][0]

	return score_dict,feat_v

### from fselect.py
### return a dict containing F_j
def cal_Fscore(labels,samples):

	data_num=float(len(samples))
	p_num = {} #key: label;  value: data num
	sum_f = [] #index: feat_idx;  value: sum
	sum_l_f = {} #dict of lists.  key1: label; index2: feat_idx; value: sum
	sumq_l_f = {} #dict of lists.  key1: label; index2: feat_idx; value: sum of square
	F={} #key: feat_idx;  valud: fscore
	max_idx = -1

	### pass 1: check number of each class and max index of features
	for p in range(len(samples)): # for every data point
		label=labels[p]
		point=samples[p]

		if label in p_num: p_num[label] += 1
		else: p_num[label] = 1

		for f in point.keys(): # for every feature
			if f>max_idx: max_idx=f
	### now p_num and max_idx are set

	### initialize variables
	sum_f = [0 for i in range(max_idx)]
	for la in p_num.keys():
		sum_l_f[la] = [0 for i in range(max_idx)]
		sumq_l_f[la] = [0 for i in range(max_idx)]

	### pass 2: calculate some stats of data
	for p in range(len(samples)): # for every data point
		point=samples[p]
		label=labels[p]
		for tuple in point.items(): # for every feature
			f = tuple[0]-1 # feat index
			v = tuple[1] # feat value
			sum_f[f] += v
			sum_l_f[label][f] += v
			sumq_l_f[label][f] += v**2
	### now sum_f, sum_l_f, sumq_l_f are done

	### for each feature, calculate f-score
	eps = 1e-12
	for f in range(max_idx):
		SB = 0
		for la in p_num.keys():
			SB += (p_num[la] * (sum_l_f[la][f]/p_num[la] - sum_f[f]/data_num)**2 )

		SW = eps
		for la in p_num.keys():
			SW += (sumq_l_f[la][f] - (sum_l_f[la][f]**2)/p_num[la]) 

		F[f+1] = SB / SW

	return F



if __name__ == "__main__":
    start = datetime.now()

    svm = AINewsSVMClassifier()
    #urlids = []
    #for i in range(0, 2000):
    #    if svm.corpus.get_article(i) != None:
    #        urlids.append(i)

    if len(sys.argv) < 3:
        print("Wrong args.")
        sys.exit()

    if sys.argv[1] == "evaluate":
        svm.evaluate(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "predict":
        svm.predict(sys.argv[2].split(',')) #svm.predict(urlids)

    print datetime.now() - start
