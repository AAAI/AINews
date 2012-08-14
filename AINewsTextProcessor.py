# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

"""
AINewsTextProcessor is used to process text into bag of words.
NLTK libarary is used to morph the words into original form. The
simpletextprocess is the key function which return the word-freqency dictionary.
textproecess is a more complicated function using PoS tagging analysis and
name entity extraction. However, it runs much slower so that it is not used
in the default configuration.
"""

import re
import types
import nltk
from AINewsConfig import config, stopwords, whitelist

class AINewsTextProcessor:
    """
    The Document class contains one document .
    Raw text is stored in the class, then text Preprocess is conducted
    and processed information are stored.
    """
    def __init__(self):
        """
        Initialize AINewsTextProcessor class
        """
        self.cache = {}
        self.stemmer = nltk.stem.PorterStemmer()
        self.whitelist_stemmed = []
        for w in whitelist:
            ws = w.split(' ')
            ws = map(lambda w: self.stem(w), ws)
            self.whitelist_stemmed.append(' '.join(ws))

    def stem(self, word):
        if word[0].islower():
            return self.stemmer.stem(word)
        else:
            return word
        
    def unigrams(self, raw, removeStopwords = True):
        """
        Extract the bag of words from the raw text.
        @param raw: the raw text to be processed.
        @type raw: C{string}
        """
        if raw =="": return []
        splitter=re.compile('\\W*')
        return [s.lower() for s in splitter.split(raw) \
                if s != '' and \
                (removeStopwords == False or s.lower() not in stopwords)]
         
    def bigrams(self, unigrams):
        """
        Generate bigrams from unigrams
        @param unigrams: unigram words
        @type unigrams: C{list}
        """
        return nltk.bigrams(unigrams)
        
    def trigrams(self, unigrams):
        """
        Generate trigrams from unigrams
        @param unigrams: unigram words
        @type unigrams: C{list}
        """
        return nltk.trigrams(unigrams)
        
    def simpletextprocess(self, urlid, raw):
        """
        Key function in AINewsTextProcessor that it extracts the bag of words,
        then each word is morphed and passed the stopword list and count
        its freqency based on the NLTK's FreqDist class.
        @param raw: the raw text to be processed.
        @type raw: C{string}
        """
        if urlid in self.cache:
            return self.cache[urlid]

        unigrams = map(lambda w: self.stem(w), self.unigrams(raw))
        self.cache[urlid] = nltk.FreqDist(unigrams)
        return self.cache[urlid]

    def whiteprocess(self, urlid, raw):
        """
        Keep only whitelisted unigrams, bigrams, and trigrams
        """
        if urlid in self.cache:
            return self.cache[urlid]

        unigrams = map(lambda w: self.stem(w), self.unigrams(raw, False))
        words_all = unigrams
        for (a,b) in self.bigrams(unigrams):
            if ' ' in a or ' ' in b: continue
            words_all.append(a + ' ' + b)
        for (a,b,c) in self.trigrams(unigrams):
            if ' ' in a or ' ' in b or ' ' in c: continue
            words_all.append(a + ' ' + b + ' ' + c)

        words = []
        for w in words_all:
            if w in self.whitelist_stemmed:
                words.append(w)
        self.cache[urlid] = nltk.FreqDist(words)
        return self.cache[urlid]
        
    
    
        
