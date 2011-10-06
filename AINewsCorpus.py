# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

import sys
import random
import math
import operator
import re
from itertools import izip
from AINewsConfig import config, paths
from AINewsDB import AINewsDB
from AINewsTextProcessor import AINewsTextProcessor
from AINewsTools import loadpickle, trunc

class AINewsCorpus:
    """
    A corpus is a set of news articles (each with a title, content,
    and categories) that are used for training and comparison
    purposes. For training, the corpus provides the training
    examples. For comparison, the corpus provides the data for various
    measures like word frequency. This is important in the prediction
    process: we only want to predict a new article's categories based
    on word frequencies, and other measures, from the corpus; we don't
    want articles that have not been "vetted" (articles not part of
    the corpus) to contribute to these measures.

    A corpus can be "loaded" via C{load_corpus()} or "restored" via
    C{restore_corpus()}. The difference is the following: when loading a
    corpus, word frequencies are measured and stored in the database
    table C{wordlist_eval}; when restoring a corpus, word frequencies
    are simply retrieved from the database table C{wordlist}. In other
    words, we load a corpus when we are training or evaluating our
    training procedures, and we restore a corpus when we are
    predicting.
    """
    def __init__(self):
        self.txtpro = AINewsTextProcessor()
        self.cache_urls = {}

        #: A dictionary of word=>word freq in corpus
        self.dftext = {}

        #: A dictionary of word=>wordid
        self.idwords = {}

        #: A dictionary of wordid=>word
        self.wordids = {}

        self.db = AINewsDB()

        self.categories = ["AIOverview","Agents", "Applications", \
                 "CognitiveScience", "Education", "Ethics", "Games", "History", \
                 "Interfaces", "MachineLearning", "NaturalLanguage", "Philosophy", \
                 "Reasoning", "Representation", "Robots", "ScienceFiction", \
                 "Speech", "Systems", "Vision"]

        self.sources = {}
        rows = self.db.selectall("select parser, relevance from sources")
        for row in rows:
            self.sources[row[0].split('::')[0]] = int(row[1])

        self.retained_db_docs = None
        
        self.restore_corpus()

    def get_relevance(self, publisher):
        if re.search(r'via Google News', publisher):
            publisher = 'GoogleNews'
        return self.sources[publisher]

    def compare_articles(self, article1, article2):
        dupcount1 = len(article1['duplicates'])
        dupcount2 = len(article2['duplicates'])
        relevance1 = self.get_relevance(article1['publisher'])
        relevance2 = self.get_relevance(article2['publisher'])
        cat_count1 = len(article1['categories'])
        cat_count2 = len(article2['categories'])
        if cmp(dupcount1, dupcount2) == 0:
            if cmp(relevance1, relevance2) == 0:
                return cmp(cat_count1, cat_count2)
            else:
                return cmp(relevance1, relevance2)
        else:
            return cmp(dupcount1, dupcount2)

    def get_tfidf(self, urlid, wordfreq):
        """
        Helper function to retrieve the tfidf of each word based on the urlid.
        @param  urlid: target news story's urlid.
        @type  urlid: C{int}
        """
        if urlid in self.cache_urls:
            return self.cache_urls[urlid]
        wordid_freq_pairs = {}
        for word in wordfreq:
            if word in self.dftext:
                wordid_freq_pairs[self.idwords[word]] = (wordfreq[word], self.dftext[word])

        data = {}
        distsq = 0.0
        for wordid in wordid_freq_pairs:
            tfidf = math.log(wordid_freq_pairs[wordid][0] + 1, 2) * \
                    (math.log(self.corpus_count + 1, 2) - \
                    math.log(wordid_freq_pairs[wordid][1] + 1, 2))
            data[wordid] = tfidf
            distsq += tfidf * tfidf
        dist = math.sqrt(distsq)
        if dist > 1.0e-9:
            for key in data:
                data[key] /= dist
        self.cache_urls[urlid] = data
        return data

    def cos_sim(self, tfidf1, tfidf2):
        """
        A helper function to compute the cos simliarity between
        news story and centroid.
        @param  tfidf1: target news story tfidf vector.
        @type  tfidf1: C{dict}
        @param tfidf2: centroid tfidf vector.
        @type  tfidf2: C{dict}
        """
        sim = 0.0
        for key in tfidf1:
            if key in tfidf2:
                word = self.wordids[key]
                a = tfidf1[key]
                b = tfidf2[key]
                sim += a*b
        return sim

    def get_article(self, urlid, corpus = False):
        row = None
        if corpus:
            table = 'cat_corpus'
            cat_table = 'cat_corpus_cats'
            row = self.db.selectone("""select u.url, u.title, u.content
                from %s as u where u.urlid = %s""" % (table, urlid))

        else:
            table = 'urllist'
            cat_table = 'categories'
            row = self.db.selectone("""select u.url, u.title, u.content, u.pubdate,
                u.crawldate, u.processed, u.published, u.publisher from %s as u where u.urlid = %s""" % \
                                        (table, urlid))
        if row != None:
            wordfreq = self.txtpro.simpletextprocess(urlid, row[2])
            processed = False
            if not corpus and row[5] == 1: processed = True
            published = False
            if not corpus and row[6] == 1: published = True
            pubdate = ""
            if not corpus: pubdate = row[3]
            crawldate = ""
            if not corpus: crawldate = row[4]
            publisher = ""
            if not corpus: publisher = row[7]
            categories = []
            cat_rows = self.db.selectall("""select category from %s
                where urlid = %s""" % (cat_table, urlid))
            for cat_row in cat_rows:
                categories.append(cat_row[0])
            return {'urlid': urlid, 'url': row[0], 'title': row[1],
                    'content': trunc(row[2], max_pos=3000),
                    'content_all': row[2],
                    'pubdate': pubdate, 'crawldate': crawldate,
                    'processed': processed, 'published': published,
                    'publisher': publisher,
                    'categories': categories, 'duplicates': [],
                    'wordfreq': wordfreq, 'tfidf': self.get_tfidf(urlid, wordfreq)}
        else:
            return None

    def get_articles_daterange(self, date_start, date_end):
        articles = {}
        rows = self.db.selectall("""select urlid from urllist
            where pubdate >= %s and pubdate <= %s""", (date_start, date_end))
        for row in rows:
            articles[row[0]] = self.get_article(row[0])
        return articles

    def get_articles_idrange(self, urlid_start, urlid_end):
        articles = {}
        rows = self.db.selectall("""select urlid from urllist
            where urlid >= %s and urlid <= %s""", (urlid_start, urlid_end))
        for row in rows:
            articles[row[0]] = self.get_article(row[0])
        return articles

    def get_unprocessed(self):
        articles = {}
        rows = self.db.selectall("select urlid from urllist where processed = 0")
        for row in rows:
            articles[row[0]] = self.get_article(row[0])
        return articles

    def mark_processed(self, articles):
        for urlid in articles:
            self.db.execute("update urllist set processed = 1 where urlid = %s",
                    urlid)

    def mark_published(self, articles):
        for article in articles:
            self.db.execute("update urllist set published = 1 where urlid = %s",
                    article['urlid'])

    def restore_corpus(self):
        self.wordids = {}
        self.dftext = {}
        rows = self.db.selectall("select rowid, word, dftext from wordlist")
        for row in rows:
            self.wordids[row[0]] = row[1]
            self.idwords[row[1]] = row[0]
            self.dftext[row[1]] = row[2]
        self.corpus_count = self.db.selectone("select count(*) from cat_corpus")[0]

    def add_freq_index(self, urlid, wordfreq, categories = []):
        for word in wordfreq:
            self.wordcounts.setdefault(word, 0)
            self.wordcounts[word] += 1

    def commit_freq_index(self, table):
        self.dftext = {}
        self.wordids = {}
        for word in self.wordcounts:
            rowid = self.db.execute("insert into "+table+" (word, dftext) " + \
                "values(%s, %s)", (word, self.wordcounts[word]))
            self.wordids[rowid] = word
            self.idwords[word] = rowid
            self.dftext[word] = self.wordcounts[word]
        self.wordcounts = {}

    def load_corpus(self, ident, pct, debug = False, retain = False):
        if debug:
            print "Loading corpus..."
        source = ident.split(':')[0]
        name = ident.split(':')[1:]
        if source == "file":
            docs = self.load_file_corpus(name, debug)
        elif source == "db":
            docs = self.load_db_corpus(name, debug, retain)
        print

        random.shuffle(docs)
        offset = int(len(docs)*pct)
        if debug:
            print "Selecting random %d%% of corpus (%d docs)." % \
                    (pct * 100, offset)

        # sort train_corpus by urlid
        train_corpus = sorted(docs[0:offset], key=operator.itemgetter(0))
        self.corpus_count = len(train_corpus)

        # sort predict_corpus by urlid
        predict_corpus = sorted(docs[offset:offset+int(len(docs)*0.1)], \
                key=operator.itemgetter(0))

        self.db.execute("delete from wordlist_eval")
        self.db.execute("alter table wordlist_eval auto_increment = 0")
        self.wordids = {}
        self.wordcounts = {}
        self.cache_urls = {}
        for c in train_corpus:
            self.add_freq_index(c[0], c[1], c[2].split())
        self.commit_freq_index('wordlist_eval')

        return (train_corpus, predict_corpus)

    def load_file_corpus(self, name, debug = False):
        wordsfile = paths['corpus.corpus_other'] + name[0] + ".mat.clabel"
        f = open(wordsfile, 'r')
        self.wordids = {}
        wordid = 1
        for line in f:
            self.wordids[int(wordid)] = line.strip()
            wordid += 1

        catsfile = paths['corpus.corpus_other'] + name[0] + ".mat.rlabel"
        f = open(catsfile, 'r')
        cats = {}
        uniqcats = set()
        docid = 0
        for line in f:
            cats[docid] = line.strip()
            uniqcats.add(line.strip())
            docid += 1
        self.categories = list(uniqcats)

        matfile = paths['corpus.corpus_other'] + name[0] + ".mat"
        f = open(matfile, 'r')
        f.readline() # ignore first line
        docs = []
        docid = 0
        for line in f:
            wordfreq = {}
            for (wordid, freq) in izip(*[iter(line.split())]*2):
                wordfreq[self.wordids[int(wordid)]] = int(float(freq))
            docs.append((docid, wordfreq, cats[docid]))
            docid += 1
            if debug:
                sys.stdout.write('.')
                sys.stdout.flush()
        return docs

    def load_db_corpus(self, name, debug = False, retain = False):
        rows = self.db.selectall("""select c.urlid, c.content,
            group_concat(cc.category separator ' ')
            from %s as c, %s as cc
            where c.urlid = cc.urlid
            group by c.urlid order by c.urlid desc""" % (name[0], name[1]))
        print "Processing %d articles..." % len(rows)
        if retain and self.retained_db_docs != None:
            return self.retained_db_docs
        docs = []
        for row in rows:
            wordfreq = self.txtpro.simpletextprocess(row[0], row[1])
            if wordfreq.N() > 0:
                docs.append((row[0], wordfreq, row[2]))
            if debug:
                sys.stdout.write('.')
                sys.stdout.flush()
        if retain:
            self.retained_db_docs = docs
        return docs

