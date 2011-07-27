
import csv
import sys
import random
import operator
from datetime import datetime
from AINewsConfig import paths
from AINewsCorpus import AINewsCorpus
from AINewsTextProcessor import AINewsTextProcessor

class AINewsTermWeightClassifier:
    def __init__(self):
        self.corpus = AINewsCorpus()
        self.txtpro = AINewsTextProcessor()

        self.threshold = 5

        csv_file = open(paths['classifier.termweights'])
        self.termweights_csv = csv.DictReader(csv_file)
        self.termweights = {}
        for row in self.termweights_csv:
            words = row['word'].strip().split(' ')
            word = ' '.join(map(lambda w: self.txtpro.stem(w), words))
            self.termweights[word] = {}
            for cat in self.corpus.categories:
                if row[cat] != '':
                    self.termweights[word][cat] = float(row[cat])
                else:
                    self.termweights[word][cat] = 0.0

    def predict(self, urlid, wordfreq, count):
        predicted = []
        similarities = {}
        for cat in self.corpus.categories:
            sim = 0.0
            for word in wordfreq:
                if word in self.termweights:
                    sim += self.termweights[word][cat]
            similarities[cat] = sim
            #if sim > self.threshold:
            #    predicted.append(cat)
        tuples = sorted(similarities.iteritems(), key=operator.itemgetter(1),
                reverse=True)
        #for c in similarities:
        #    if similarities[c] > 0:
        #        predicted.append(c)
        predicted = map(lambda x: x[0], tuples[0:count])
        return (predicted, similarities)

    def evaluate(self, ident):
        random.seed()
        results = {}
        iteration = 0
        iterations = 21
        (corpus, _) = self.corpus.load_corpus(ident, 1.0, True)
        for thresh in range(4, 5, 1):
            self.threshold = thresh
            iteration += 1
            truepos = 0
            falsepos = 0
            trueneg = 0
            falseneg = 0
            pos = 0
            catcount = 0
            truecatcount = 0
            anymatched = 0
            for c in corpus:
                truecats = c[2].split(' ')
                truecatcount += len(truecats)
                (predicted, similarities) = self.predict(c[0], c[1], len(truecats))
                catcount += len(predicted)
                pos += len(truecats)
                #print c[0]
                #print similarities
                #print predicted
                #print truecats
                if len(set(predicted) & set(truecats)) > 0:
                    anymatched += 1
                for cat in self.corpus.categories:
                    if cat in truecats and cat in predicted:
                        truepos += 1
                    if cat not in truecats and cat in predicted:
                        falsepos += 1
                    if cat not in truecats and cat not in predicted:
                        trueneg += 1
                    if cat in truecats and cat not in predicted:
                        falseneg += 1
            precision = float(truepos)/(truepos + falsepos)
            recall = float(truepos)/pos
            f1 = 2.0 * (precision * recall) / (precision + recall)
            print anymatched
            print "%d/%d Threshold %d: %d TP, %d FP, %d TN, %d FN" % \
                (iteration, iterations, self.threshold, \
                truepos, falsepos, trueneg, falseneg)
            print ("\tprec = %.2f, recall = %.2f, f1 = %.2f, " + \
                "avg cats = %.2f, avg true cats = %.2f") % \
                (precision, recall, f1, float(catcount)/len(corpus), \
                float(truecatcount)/len(corpus))
            print
            results[self.threshold] = (truepos, falsepos, trueneg, falseneg, \
                    precision, recall, f1)
        #(mean, std) = meanstdv(matched_results)
        #print "Mean: %.2f, stddev: %.2f" % (mean, std)

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

    cat = AINewsTermWeightClassifier()

    if len(sys.argv) < 3:
        print ("Provide 'evaluate db:cat_corpus:cat_corpus_cats'" +
            " or 'evaluate file:oh10'")
        sys.exit()

    cat.evaluate(sys.argv[2])

    print datetime.now() - start

