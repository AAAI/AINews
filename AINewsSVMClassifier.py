
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

    def predict(self, urlids):
        self.corpus.restore_corpus()

        # produce the test input file
        f = open(paths['svm.svm_data']+'predict', 'w')
        for urlid in urlids:
            wordfreq = self.corpus.get_article(urlid)['wordfreq']
            tfidf = self.corpus.get_tfidf(urlid, wordfreq)
            f.write("+1 ")
            for wordid in sorted(tfidf.keys()):
                f.write("%s:%f " % (wordid, tfidf[wordid]))
            f.write("\n")
        f.close()

        predictions = {}
        for urlid in urlids:
            predictions[urlid] = []

        for cat in self.corpus.categories:
            cmd = 'svm-scale -r "%s" "%s" > "%s"' % \
                (paths['svm.svm_data']+cat+'.range', \
                paths['svm.svm_data']+'predict', \
                paths['svm.svm_data']+'predict-'+cat+'.scaled')
            Popen(cmd, shell = True).wait()
            cmd = 'svm-predict "%s" "%s" "%s" > /dev/null' % \
                (paths['svm.svm_data']+'predict-'+cat+'.scaled', \
                paths['svm.svm_data']+cat+'.model',
                paths['svm.svm_data']+'predict-'+cat+'.output')
            Popen(cmd, shell = True).wait()
            f = open(paths['svm.svm_data']+'predict-'+cat+'.output', 'r')
            lines = f.readlines()
            f.close()
            for i in range(len(lines)):
                if lines[i] == "1\n":
                    predictions[urlids[i]].append(cat)

        for urlid in urlids:
            title = self.corpus.get_article(urlid)['title']
            print "%s %s:\n\t%s\n" % (urlid, title, predictions[urlid])

    def evaluate(self, ident):
        results = {}
        (train_corpus, predict_corpus) = self.corpus.load_corpus(ident, 1.0, True)
        self.generate_libsvm_input(train_corpus, 'train')
        self.generate_libsvm_input(predict_corpus, 'predict')
        print "Done generating SVM input."
        results = self.libsvm_train()
        print results

    def generate_libsvm_input(self, corpus, suffix):
        for cat in self.corpus.categories:
            model = open(paths['svm.svm_data']+cat+'-'+suffix, 'w')
            model.close()
        for c in corpus:
            cats = c[2].split(' ')
            tfidf = self.corpus.get_tfidf(c[0], c[1])
            for cat in self.corpus.categories:
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
        for cat in self.corpus.categories:
            sys.stdout.write("Training and testing " + cat + "... ")
            sys.stdout.flush()
            cmd = 'python svm-easy.py "%s" "%s"' % \
                    (paths['svm.svm_data']+cat+'-train.txt',
                    paths['svm.svm_data']+cat+'-predict.txt')
            (stdout, _) = Popen(cmd, shell = True, stdout=PIPE).communicate()
            m = re.match('.*Accuracy = (\d+).*', re.sub('\n', '', stdout))
            results[cat] = float(m.group(1))
            sys.stdout.write(str(results[cat]) + "\n")
            sys.stdout.flush()
        return results;

if __name__ == "__main__":
    start = datetime.now()

    svm = AINewsSVMClassifier()
    urlids = []
    for i in range(0, 2000):
        if svm.corpus.get_article(i) != None:
            urlids.append(i)

    if len(sys.argv) < 3:
        print("Wrong args.")
        sys.exit()

    if sys.argv[1] == "evaluate":
        svm.evaluate(sys.argv[2])
    elif sys.argv[1] == "predict":
        svm.predict(urlids) #sys.argv[2].split(','))

    print datetime.now() - start
