# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

from operator import itemgetter
import nltk.data
from subprocess import *
import sys
import os

from AINewsConfig import stopwords, paths
from AINewsCorpus import AINewsCorpus

class AINewsSummarizer:
    def __init__(self):
        self.sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

    def reorder_sentences(self, output_sentences, content):
        output_sentences.sort(lambda s1, s2:
            content.find(s1) - content.find(s2))
        return output_sentences

    def summarize_single_ots(self, article):
        f = open(paths['ainews.output'] + 'content.txt', 'w')
        f.write(article['content'])
        f.close()
        (stdout, _) = Popen("%s -r 30 %s" % (paths['libraries.ots'], (paths['ainews.output'] + 'content.txt')), \
                                shell = True, stdout=PIPE).communicate()
        sentences = self.sent_detector.tokenize(stdout)
        return sentences[:4]

    def summarize(self, corpus, articles):
        for urlid in articles:
            articles[urlid]['summary'] = \
                (" ".join(self.summarize_single_ots(articles[urlid]))).strip()
    
    def summarize_article(self, corpus, article, num_sentences, joined = True):
        sorted_tfidf = sorted(article['tfidf'].iteritems(), key=itemgetter(1),
                reverse = True)
        best_words = [corpus.wordids[pair[0]] for pair in sorted_tfidf[:10]]

        # break the input up into sentences.  working_sentences is used 
        # for the analysis, but actual_sentences is used in the results
        # so capitalization will be correct.
        
        actual_sentences = self.sent_detector.tokenize(article['content'])
        working_sentences = [sentence.lower() for sentence in actual_sentences]

        # iterate over the most frequent words, and add the first sentence
        # that inclues each word to the result.
        output_sentences = []

        for word in best_words:
            for i in range(0, len(working_sentences)):
                if (word in working_sentences[i] and actual_sentences[i] not in output_sentences):
                    output_sentences.append(actual_sentences[i])
                    break
                if len(output_sentences) >= num_sentences: break
            if len(output_sentences) >= num_sentences: break
            
        # sort the output sentences back to their original order
        output_sentences = self.reorder_sentences(output_sentences, article['content'])

        if joined:
            # concatinate the sentences into a single string
            return " ".join(output_sentences)
        else:
            return output_sentences

    def evaluate(self, ident, inputdir):
        corpus = AINewsCorpus()
        (articles, _) = corpus.load_corpus(ident, 1.0, True)
        for (urlid,_,_) in articles:
            article = corpus.get_article(urlid, True)
            try:
                os.mkdir("%s/gold/%s" % (inputdir, urlid))
            except:
                pass
            f = open("%s/gold/%s/%s.fulltext" % (inputdir, urlid, urlid), 'w')
            f.write(article['content'])
            f.write("\n")
            f.close()
            f = open("%s/system/ots/%s.ots.system" % (inputdir, urlid), 'w')
            f.write("\n".join(self.summarize_single_ots(article)))
            f.write("\n")
            f.close()
            f = open("%s/system/tfidf/%s.tfidf.system" % (inputdir, urlid), 'w')
            f.write("\n".join(self.summarize_article(corpus, article, 4, False)))
            f.write("\n")
            f.close()
            print "Saved %s." % urlid

if __name__ == "__main__":
    summarizer = AINewsSummarizer()

    if sys.argv[1] == "evaluate":
        summarizer.evaluate(sys.argv[2], sys.argv[3])
