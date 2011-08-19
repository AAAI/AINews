# Simple Summarizer 
# Copyright (C) 2010 Tristan Havelick 
# Author: Tristan Havelick <tristan@havelick.com>
# URL: <http://www.tristanhavelick.com>
# $Id$
"""
A summarizer based on the algorithm found in Classifier4J by Nick Lothan.      
In order to summarize a document this algorithm first determines the 
frequencies of the words in the document.  It then splits the document
into a series of sentences.  Then it creates a summary by including the
first sentence that includes each of the most frequent words.  Finally
summary's sentences are reordered to reflect that of those in the original 
document.
Original Author: Tristan Havelick
Modified by: Liang Dong
original code url: http://tristanhavelick.com/summarize.zip
"""

from operator import itemgetter
from nltk.probability import FreqDist 
from nltk.tokenize import RegexpTokenizer
import nltk.data

from AINewsConfig import stopwords

class AINewsSummarizer:
    def __init__(self):
        pass

    def reorder_sentences(self, output_sentences, content):
        output_sentences.sort(lambda s1, s2:
            content.find(s1) - content.find(s2))
        return output_sentences

    def summarize(self, corpus, articles):
        for urlid in articles:
            articles[urlid]['summary'] = \
                self.summarize_article(corpus, articles[urlid], 4)
    
    def summarize_article(self, corpus, article, num_sentences):
        sorted_tfidf = sorted(article['tfidf'].iteritems(), key=itemgetter(1),
                reverse = True)
        best_words = [corpus.wordids[pair[0]] for pair in sorted_tfidf[:10]]

        # break the input up into sentences.  working_sentences is used 
        # for the analysis, but actual_sentences is used in the results
        # so capitalization will be correct.
        
        sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
        actual_sentences = sent_detector.tokenize(article['content'])
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

        # concatinate the sentences into a single string
        return " ".join(output_sentences)
