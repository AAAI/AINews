
import sys
import random
import re
from datetime import datetime
from subprocess import *
from AINewsConfig import paths
from AINewsCorpus import AINewsCorpus

class AINewsSVMClassifier:
    def __init__(self):
        self.corpus = AINewsCorpus()

    def predict(self, urlid, wordfreq):
        pass

    def evaluate(self, ident):
        random.seed()
        results = {}
        iteration = 0
        (train_corpus, predict_corpus) = self.corpus.load_corpus(ident, 0.6, True)
        self.generate_libsvm_input(train_corpus, 'train')
        self.generate_libsvm_input(predict_corpus, 'predict')
        print "Done generating SVM input."
        results = self.libsvm_train()
        print results

    def generate_libsvm_input(self, corpus, suffix, multiclass):
#        for cat in self.corpus.categories:
#            model = open(paths['svm.svm_data']+cat+'-'+suffix+'.txt', 'w')
#            model.close()
        model = open(paths['svm.svm_data']+'all_cats-'+suffix+'.txt', 'w')
        for c in corpus:
            #cats = c[2].split(' ')
            cat = c[2]
            catid = 0
            i = 0
            for cat2 in self.corpus.categories:
                if cat2 == cat:
                    catid = i
                    break
                i += 1
            tfidf = self.corpus.get_tfidf(c[0], c[1])
            line = str(catid) + " "
            # wordids must be in ascending order for libsvm2
            for wordid in sorted(tfidf.keys()):
                line += "%s:%f " % (wordid, tfidf[wordid])
            model.write(line + "\n")
#            for cat in self.corpus.categories:
#                model = open(paths['svm.svm_data']+cat+'-'+suffix+'.txt', 'a')
#                if cat in cats:
#                    line = "+1 "
#                else:
#                    line = "-1 "
#                # wordids must be in ascending order for libsvm2
#                for wordid in sorted(tfidf.keys()):
#                    line += "%s:%f " % (wordid, tfidf[wordid])
#                model.write(line + "\n")
#                model.close()
        model.close()

    def libsvm_train(self):
        results = {}
        cmd = 'python svm-easy.py "%s" "%s"' % \
                (paths['svm.svm_data']+'all_cats-train.txt',
                paths['svm.svm_data']+'all_cats-predict.txt')
        Popen(cmd, shell = True).wait()
        #results[cat] = float(m.group(1))
        #sys.stdout.write(str(results[cat]) + "\n")
        #sys.stdout.flush()
#        for cat in self.corpus.categories:
#            sys.stdout.write("Training and testing " + cat + "... ")
#            sys.stdout.flush()
#            cmd = 'python svm-easy.py "%s" "%s"' % \
#                    (paths['svm.svm_data']+cat+'-train.txt',
#                    paths['svm.svm_data']+cat+'-predict.txt')
#            (stdout, _) = Popen(cmd, shell = True, stdout=PIPE).communicate()
#            m = re.match('.*Accuracy = (\d+).*', re.sub('\n', '', stdout))
#            results[cat] = float(m.group(1))
#            sys.stdout.write(str(results[cat]) + "\n")
#            sys.stdout.flush()
        return results;

if __name__ == "__main__":
    start = datetime.now()

    svm = AINewsSVMClassifier()

    if len(sys.argv) < 3:
        print("Wrong args.")
        sys.exit()

    svm.evaluate(sys.argv[2])

    print datetime.now() - start
