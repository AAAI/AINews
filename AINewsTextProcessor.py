"""
AINewsTextProcessor is used to process text into bag of words.
NLTK libarary is used to morph the words into original form. The
simpletextprocess is the key function which return the word-freqency dictionary.
textproecess is a more complicated function using PoS tagging analysis and
name entity extraction. However, it runs much slower so that it is not used
in the default configuration.
"""

import re
import nltk
import types
from nltk.corpus import wordnet as wn
from AINewsConfig import config, stopwords, cat_whitelist

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
        self.debug = config['ainews.debug']
        self.cache = {}
        self.stemmer = nltk.stem.PorterStemmer()

    def stem(self, word):
        if word[0].islower():
            return self.stemmer.stem(word)
        else:
            return word
        
    def unigrams(self, raw):
        """
        Extract the bag of words from the raw text.
        @param raw: the raw text to be processed.
        @type raw: C{string}
        """
        if raw =="": return []
        splitter=re.compile('\\W*')
        return [s.lower() for s in splitter.split(raw) \
                if s != '' and s.lower() not in stopwords]
         
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

        unigrams = map(lambda w: self.stem(w), self.unigrams(raw))
        words_all = unigrams
        for (a,b) in self.bigrams(unigrams):
            if ' ' in a or ' ' in b: continue
            words_all.append(a + ' ' + b)
        for (a,b,c) in self.trigrams(unigrams):
            if ' ' in a or ' ' in b or ' ' in c: continue
            words_all.append(a + ' ' + b + ' ' + c)

        words = []
        for w in words_all:
            if w.lower() in cat_whitelist:
                words.append(w.lower())
        self.cache[urlid] = nltk.FreqDist(words)
        return self.cache[urlid]
        
    def textprocess(self, raw, onlyNOUN = True):
        """
        My re-implementation of the preprocess by utilizing PoS tag. It combines
        both Name Entity and Unigrams into the same frequency distribution.
        @param raw: the raw text to be processed.
        @type raw: C{string}
        @param onlyNOUN: only measure name entity and nouns in the raw text
        @type onlyNOUN: C{boolean}
        """
        NN_words = []
        VB_words = []
        JJ_words = []
        NE_words = []
        
        sentences = nltk.sent_tokenize(raw)
        sentences = [nltk.word_tokenize(sent) for sent in sentences]
        sentences = [nltk.pos_tag(sent) for sent in sentences]
        self.tagged_sentences = [nltk.ne_chunk(sent, binary=True) \
                                    for sent in sentences]
        for tagged_sent in self.tagged_sentences:
            if self.debug: pass #print tagged_sent
            for tagged_token in tagged_sent:
                if type(tagged_token[0]) == types.TupleType :
                    name_entity = ""
                    for i in range(len(tagged_token)):
                        name_entity += tagged_token[i][0] + ' '
                    if len(name_entity) > 3 and len(name_entity) <= 7:
                        NE_words.append(name_entity[:-1])
                else:
                    pos = tagged_token[1][:2]
                    if pos == 'NN':
                        NN_words.append(tagged_token[0])
                    elif pos == 'VB':
                        VB_words.append(tagged_token[0])
                    elif pos == 'JJ':
                        JJ_words.append(tagged_token[0])
          
        NN_words = self.__pos_morphy(NN_words, wn.NOUN)
        if onlyNOUN == True:
            unigram_words = [w.lower() for w in NN_words \
                            if len(w)>2 and w.find('\'') == -1
                                and w.lower() not in stopwords
                                and not w.isdigit()]
        else:
            VB_words = self.__pos_morphy(VB_words, wn.VERB)
            JJ_words = self.__pos_morphy(JJ_words, wn.ADJ)
            unigram_words = [w.lower() for w in NN_words + VB_words + JJ_words \
                            if len(w)>2 and w.find('\'') == -1
                                and  w.lower() not in stopwords
                                and not w.isdigit()]
      
        #self.freqdist = nltk.FreqDist(unigram_words + NE_words)
        #return unigram_words + NE_words
        return nltk.FreqDist(unigram_words + NE_words)
        
    def __pos_morphy(self, words, pos):
        """
        Helper function to morph the words by PoS tag. It is called by
        textprocess funciton.
        @param words: the target word list to be morphed
        @type words: L{string}
        @param pos: NTLK's wordnet's POS tags (wn.NOUN, wn.VERB)
        @type pos: C{int}
        """
        res = []
        for word in words:
            morphied = wn.morphy(word, pos)
            if morphied != None:
                res.append(morphied)
            else:
                res.append(word)
        return res
    
    def simple_pos_morphy(self, word):
        """
        Helper funcion for simpletextprocess function. It doesn't process
        the PoS tagging in the first place.
        @param word: the raw word before morph
        @type word: C{string}
        """
        morphied = wn.morphy(word, wn.NOUN)
        if morphied != None:
            return morphied
        else:
            morphied = wn.morphy(word, wn.VERB)
            if morphied != None:
                return morphied
        return word
    
    
        

