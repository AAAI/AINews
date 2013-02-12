# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

import re
import pickle
import arff
import csv
from nltk.probability import FreqDist
from os import listdir, remove
from subprocess import *
from AINewsCorpus import AINewsCorpus
from AINewsConfig import config, paths
from AINewsTextProcessor import AINewsTextProcessor

class AINewsWekaClassifier:
    def __init__(self):
        self.txtpro = AINewsTextProcessor()

    def __save_bag_of_words(self, tid, fieldidx):
        # find all unique words in the arff 'title' field, remove stop
        # words, perform stemming, collect their frequencies
        phrases = []
        f = arff.load(open("%s%d.arff" % (paths['weka.training_arff_dir'], tid), 'r'))
        for record in f['data']:
            phrases.append(record[fieldidx])
        bag = self.txtpro.simpletextprocess(0, ' '.join(phrases))
        smallerbag = FreqDist()
        i = 0
        for word in bag:
            if i == 1000:
                break
            smallerbag[word] = bag[word]
            i += 1
        p = open("%sbag_of_words-%d.pickle" % (paths['weka.bag_of_words_dir'], fieldidx), 'w')
        pickle.dump(smallerbag, p)
        p.close()

    def __prepare_arff(self, tid):
        p = open("%sbag_of_words-0.pickle" % paths['weka.bag_of_words_dir'], 'r')
        bag_title = pickle.load(p)
        p.close()
        p = open("%sbag_of_words-1.pickle" % paths['weka.bag_of_words_dir'], 'r')
        bag_body = pickle.load(p)
        p.close()

        data = {'attributes': [], 'data': [], 'description': u'', 'relation': tid}
        for word in bag_title:
            data['attributes'].append(("title-%s" % word, 'NUMERIC'))
        for word in bag_body:
            data['attributes'].append(("body-%s" % word, 'NUMERIC'))
        data['attributes'].append(('class', ['yes', 'no']))

        f = arff.load(open("%s%d.arff" % (paths['weka.training_arff_dir'], tid), 'r'))
        for record in f['data']:
            record_bag_title = self.txtpro.simpletextprocess(0, record[0])
            record_bag_body = self.txtpro.simpletextprocess(0, record[1])
            record_data = []
            # iterate through original bag, figure out freq in this record's bag
            for word in bag_title:
                if word in record_bag_title:
                    record_data.append(record_bag_title[word])
                else:
                    record_data.append(0)
            for word in bag_body:
                if word in record_bag_body:
                    record_data.append(record_bag_body[word])
                else:
                    record_data.append(0)
            record_data.append(record[2])
            data['data'].append(record_data)

        fnew = open("%s%d-wordvec-nonsparse.arff" % \
                        (paths['weka.training_arff_dir'], tid), 'w')
        arff.dump(fnew, data)
        fnew.close()

        # convert to sparse format
        Popen(("java -cp %s weka.filters.unsupervised.instance.NonSparseToSparse " +
               "-i %s%d-wordvec-nonsparse.arff -o %s%d-wordvec.arff") % \
                  (paths['weka.weka_jar'],
                   paths['weka.training_arff_dir'], tid,
                   paths['weka.training_arff_dir'], tid),
              shell = True).communicate()

        remove("%s%d-wordvec-nonsparse.arff" % (paths['weka.training_arff_dir'], tid))
        
    # 1. load unprocessed arff files, from just one tid, from family_resemblance export
    # 2. gather all titles, parse into a bag of words
    # 3. save bag of words (list? need to keep the order) in a pickle file
    # 4. write new sparse arff files for each tid using this sorted bag of words

    def __get_tids(self):
        tids = []
        files = listdir(paths['weka.training_arff_dir'])
        for f in files:
            m = re.match(r'^(\d+).arff$', f)
            if m:
                if m.group(1) == '0': continue
                tids.append(int(m.group(1)))
        return tids

    def train(self):
        tids = self.__get_tids()
        
        # all tid arffs have same entries, so use the first to grab the bag of words
        print "Saving bag of words..."
        self.__save_bag_of_words(tids[0], 0)
        self.__save_bag_of_words(tids[0], 1)

        for tid in sorted(tids):
            print "Preparing tid %d" % tid
            self.__prepare_arff(tid)

        for tid in sorted(tids):
            print "Spread subsampling for tid %d" % tid
            Popen(("java -cp %s weka.filters.supervised.instance.SpreadSubsample " +
                   "-M 1.0 -X 0.0 -S 1 -c last " +
                   "-i %s%d-wordvec.arff -o %s%d-wordvec-subsample.arff") % \
                      (paths['weka.weka_jar'],
                       paths['weka.training_arff_dir'], tid,
                       paths['weka.training_arff_dir'], tid),
                  shell = True).communicate()

            print "Training random forests for tid %d" % tid
            Popen(("java -cp %s %s %s -v " +
                   "-t %s%d-wordvec-subsample.arff -d %s%d.model") % \
                      (paths['weka.weka_jar'],
                       config['weka.classifier'],
                       config['weka.classifier_params'],
                       paths['weka.training_arff_dir'], tid,
                       paths['weka.training_arff_dir'], tid),
                  shell = True, stdout = PIPE).communicate()
            print out

    def train_experiment(self):
        model_scores = {}
        models = {'random-forest': ('weka.classifiers.trees.RandomForest', '-I 20 -K 0'),
                  'naive-bayes': ('weka.classifiers.bayes.NaiveBayes', ''),
                  'bayesnet': ('weka.classifiers.bayes.BayesNet', ''),
                  'j48': ('weka.classifiers.trees.J48', ''),
                  'knn': ('weka.classifiers.lazy.IBk', '-K 3')}

        tids = self.__get_tids()
        
        # all tid arffs have same entries, so use the first to grab the bag of words
        print "Saving bag of words..."
        self.__save_bag_of_words(tids[0], 0)
        self.__save_bag_of_words(tids[0], 1)

        for tid in sorted(tids):
            print "Preparing tid %d" % tid
            self.__prepare_arff(tid)

        for tid in sorted(tids):
            print "Spread subsampling for tid %d" % tid
            Popen(("java -cp %s weka.filters.supervised.instance.SpreadSubsample " +
                   "-M 1.0 -X 0.0 -S 1 -c last " +
                   "-i %s%d-wordvec.arff -o %s%d-wordvec-subsample.arff") % \
                      (paths['weka.weka_jar'],
                       paths['weka.training_arff_dir'], tid,
                       paths['weka.training_arff_dir'], tid),
                  shell = True).communicate()

        for tid in sorted(tids):
            model_scores[tid] = {}
            for model in models.keys():
                print "Training %s for tid %d" % (models[model][0], tid)
                (out, _) = Popen(("java -cp %s %s %s -v " +
                                  "-t %s%d-wordvec-subsample.arff -d %s%d.model") % \
                                     (paths['weka.weka_jar'],
                                      models[model][0], models[model][1],
                                      paths['weka.training_arff_dir'], tid,
                                      paths['weka.training_arff_dir'], tid),
                                 shell = True, stdout = PIPE).communicate()
                
                correct = 0.0
                for line in out.splitlines():
                    m = re.search(r'Correctly Classified Instances\s+\d+\s+(.*) %', line)
                    if m:
                        correct = float(m.group(1))
                        break
                model_scores[tid][model] = correct

        with open('training_experiment.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['model', 'tid', 'correct'])
            for tid in model_scores.keys():
                for model in model_scores[tid].keys():
                    writer.writerow([model, tid, model_scores[tid][model]])

    def __predict_arff(self):
        tids = self.__get_tids()

        # the testing file should always be 0.arff
        self.__prepare_arff(0)

        predictions = {}
        for tid in sorted(tids):
            predictions[tid] = []

            print "Predicting tid %d" % tid
            (out, err) = Popen(("java -cp %s %s " +
                                "-T %s0-wordvec.arff -l %s%d.model -p last") % \
                                   (paths['weka.weka_jar'],
                                    config['weka.classifier'],
                                    paths['weka.training_arff_dir'],
                                    paths['weka.training_arff_dir'], tid),
                               shell = True, stdout = PIPE).communicate()
            for line in out.splitlines():
                m = re.search(r'2:no\s+[12]:(no|yes)\s+\+?\s+(\d+\.?\d*)', line)
                if m:
                    answer = False
                    if m.group(1) == 'yes':
                        answer = True
                    conf = float(m.group(2))
                    if conf < 0.75:
                        answer = False
                    predictions[tid].append((answer, conf))
        return predictions

    def predict(self, articles):
        # modifies the provided articles dict

        data = {'attributes': [('title', 'STRING'),
                               ('body', 'STRING'),
                               ('class', ['yes', 'no'])],
                'data': [], 'description': u'', 'relation': '0'}

        for urlid in sorted(articles.keys()):
            title = re.sub(r'\W', ' ', articles[urlid]['title'])
            body = re.sub(r'\W', ' ', articles[urlid]['summary'])
            data['data'].append([title, body, 'no'])

        # make the testing file 0.arff
        fnew = open("%s0.arff" % paths['weka.training_arff_dir'], 'w')
        arff.dump(fnew, data)
        fnew.close()

        predictions = self.__predict_arff()

        for urlid in sorted(articles.keys()):
            articles[urlid]['categories'] = []

        tids = self.__get_tids()
        for tid in sorted(tids):
            for (i, urlid) in enumerate(sorted(articles.keys())):
                if predictions[tid][i][0]:
                     articles[urlid]['categories'].append(str(tid))

