
import sys
import re
from datetime import datetime
from subprocess import *
from svmutil import *
from AINewsConfig import paths
from AINewsCorpus import AINewsCorpus
from AINewsTools import loadfile

class AINewsSVMClassifier:
    def __init__(self):
        self.corpus = AINewsCorpus()
        self.categories = self.corpus.categories
        #self.categories.append('NotRelated')

    def predict(self, articles):
        urlids = sorted(articles.keys())
        for urlid in articles:
            articles[urlid]['categories'] = []

        # produce the test input file
        f = open(paths['svm.svm_data']+'predict', 'w')
        for urlid in urlids:
            for cat in self.categories:
                articles[urlid]['cat_probs'] = {}
            tfidf = self.corpus.get_tfidf(urlid, articles[urlid]['wordfreq'])
            f.write("+1 ")
            for wordid in sorted(tfidf.keys()):
                f.write("%s:%f " % (wordid, tfidf[wordid]))
            f.write("\n")
        f.close()

        # predict each category plus NotRelated
        for cat in self.categories:
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

    def evaluate(self, ident):
        results = {}
        (train_corpus, predict_corpus) = self.corpus.load_corpus(ident, 0.9, True)
        self.generate_libsvm_input(train_corpus, 'train')
        self.generate_libsvm_input(predict_corpus, 'predict')
        print "Done generating SVM input."
        results = self.libsvm_train()
        print results

    def generate_libsvm_input(self, corpus, suffix):
        # erase files before appending
        for cat in self.categories:
            model = open(paths['svm.svm_data']+cat+'-'+suffix, 'w')
            model.close()
        for c in corpus:
            cats = c[2].split(' ')
            tfidf = self.corpus.get_tfidf(c[0], c[1])
            # build an input set for each category plus NotRelated
            for cat in self.categories:
                model = open(paths['svm.svm_data']+cat+'-'+suffix, 'a')
                if cat in cats:
                    line = "+1 "
                else:
                    line = "-1 "
                # wordids must be in ascending order for libsvm2
                for wordid in sorted(tfidf.keys()):
                    line += "%s:%f " % (wordid, tfidf[wordid])
                model.write(line + "\n")
                model.close()

    def libsvm_train(self):
        results = {}
        # train each category plus NotRelated
        for cat in self.categories:
            sys.stdout.write("Training and testing " + cat + "... ")
            sys.stdout.flush()
            cmd = 'python svm-easy.py "%s" "%s"' % \
                    (paths['svm.svm_data']+cat+'-train',
                    paths['svm.svm_data']+cat+'-predict')
            (stdout, _) = Popen(cmd, shell = True, stdout=PIPE).communicate()
            m = re.match('.*Accuracy = (\d+).*', re.sub('\n', '', stdout))
            results[cat] = float(m.group(1))
            sys.stdout.write(str(results[cat]) + "\n")
            sys.stdout.flush()
        return results;

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
        svm.evaluate(sys.argv[2])
    elif sys.argv[1] == "predict":
        svm.predict(sys.argv[2].split(',')) #svm.predict(urlids)

    print datetime.now() - start
