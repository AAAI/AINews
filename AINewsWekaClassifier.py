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
from os import listdir, remove
from subprocess import *
from AINewsCorpus import AINewsCorpus
from AINewsConfig import config, paths
from AINewsTextProcessor import AINewsTextProcessor

class AINewsWekaClassifier:
    def __init__(self):
        self.txtpro = AINewsTextProcessor()

    def classify_many(self, articles):
        # create arff file
        arff = open("%snewsfinder.arff" % paths['weka.tmp_arff_dir'], 'w')
        arff.write("@relation newsfinder\n")
        arff.write("@attribute title string\n")
        arff.write("@attribute class {1,0}\n")
        arff.write("@data\n")

        sorted_urlids = sorted(articles.keys())
        for urlid in sorted_urlids:
            title = re.sub(r'\'', '', articles[urlid]['title'])
            arff.write("'%s',0\n" % title)

        Popen("java -cp %s %s -i %snewsfinder.arff -o %snewsfinder-wordvec.arff" % \
                  (paths['weka.weka_jar'], config['weka.wordvec_params'],
                   paths['weka.tmp_arff_dir'], paths['weka.tmp_arff_dir']),
              shell = True).communicate()

        print "java -cp %s %s -i %snewsfinder-wordvec.arff -o %snewsfinder-reorder.arff" % \
                  (paths['weka.weka_jar'], config['weka.reorder_params'],
                   paths['weka.tmp_arff_dir'], paths['weka.tmp_arff_dir'])

        Popen("java -cp %s %s -i %snewsfinder-wordvec.arff -o %snewsfinder-reorder.arff" % \
                  (paths['weka.weka_jar'], config['weka.reorder_params'],
                   paths['weka.tmp_arff_dir'], paths['weka.tmp_arff_dir']),
              shell = True).communicate()

    def __save_bag_of_words(self, tid):
        # find all unique words in the arff 'title' field, remove stop
        # words, perform stemming, collect their frequencies
        titles = []
        f = arff.load(open("%s%d.arff" % (paths['weka.training_arff_dir'], tid), 'r'))
        for record in f['data']:
            titles.append(record[0])
        bag = self.txtpro.simpletextprocess(0, ' '.join(titles))
        p = open(paths['weka.bag_of_words'], 'w')
        pickle.dump(bag, p)
        p.close()

    def __prepare_arff(self, tid):
        # read titles from the arff, create a new arff with word vectors
        p = open(paths['weka.bag_of_words'], 'r')
        bag = pickle.load(p)
        p.close()

        data = {'attributes': [], 'data': [], 'description': u'', 'relation': tid}
        for word in bag:
            data['attributes'].append(("title-%s" % word, 'NUMERIC'))
        data['attributes'].append(('class', ['yes', 'no']))

        f = arff.load(open("%s%d.arff" % (paths['weka.training_arff_dir'], tid), 'r'))
        for record in f['data']:
            record_bag = self.txtpro.simpletextprocess(0, record[0])
            record_data = []
            # iterate through original bag, figure out freq in this record's bag
            for word in bag:
                if word in record_bag:
                    record_data.append(record_bag[word])
                else:
                    record_data.append(0)
            record_data.append(record[1])
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
        self.__save_bag_of_words(tids[0])

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
            (out, err) = Popen(("java -cp %s weka.classifiers.trees.RandomForest " +
                                "-I 20 -K 0 -v " +
                                "-t %s%d-wordvec-subsample.arff -d %s%d.model") % \
                                   (paths['weka.weka_jar'],
                                    paths['weka.training_arff_dir'], tid,
                                    paths['weka.training_arff_dir'], tid),
                               shell = True, stdout = PIPE).communicate()
            print out

    def __predict_arff(self):
        tids = self.__get_tids()

        # the testing file should always be 0.arff
        self.__prepare_arff(0)

        predictions = {}
        for tid in sorted(tids):
            predictions[tid] = []

            print "Predicting tid %d" % tid
            (out, err) = Popen(("java -cp %s weka.classifiers.trees.RandomForest " +
                                "-T %s0-wordvec.arff -l %s%d.model -p last") % \
                                   (paths['weka.weka_jar'],
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

        data = {'attributes': [('title', 'STRING'), ('class', ['yes', 'no'])],
                'data': [], 'description': u'', 'relation': '0'}

        for urlid in sorted(articles.keys()):
            title = re.sub(r'\W', ' ', articles[urlid]['title'])
            title = re.sub(r'\s+', ' ', title)
            data['data'].append([title, 'no'])

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

