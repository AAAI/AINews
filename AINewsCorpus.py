
import sys
import random
import math
import operator
from itertools import izip
from AINewsConfig import config, paths
from AINewsDB import AINewsDB
from AINewsTextProcessor import AINewsTextProcessor
from AINewsTools import loadpickle

class AINewsCorpus:
    def __init__(self):
        self.txtpro = AINewsTextProcessor()
        self.cache_urls = {}

        self.wordlist = {}
        self.wordids = {}

        self.db = AINewsDB()

        self.categories =["AIOverview","Agents", "Applications", \
                 "CognitiveScience","Education","Ethics", "Games", "History",\
                 "Interfaces","MachineLearning","NaturalLanguage","Philosophy",\
                 "Reasoning","Representation", "Robots","ScienceFiction",\
                 "Speech", "Systems","Vision"]
        
        self.restore_corpus()

    def get_tfidf(self, urlid, wordfreq):
        """
        Helper function to retrieve the tfidf of each word based on the urlid.
        @param  urlid: target news story's urlid.
        @type  urlid: C{int}
        """
        if urlid in self.cache_urls:
            return self.cache_urls[urlid]
        wordids = {}
        for word in wordfreq:
            if word in self.dftext:
                wordids[self.dftext[word][0]] = (wordfreq[word], self.dftext[word][1])

        data = {}
        distsq = 0.0
        for wordid in wordids:
            tfidf = math.log(wordids[wordid][0] + 1, 2) * \
                    (math.log(self.corpus_count, 2) - \
                    math.log(wordids[wordid][1] + 1, 2))
            data[wordid] = tfidf
            distsq += tfidf * tfidf
        dist = math.sqrt(distsq)
        if dist > 1.0e-9:
            for key in data:
                data[key] /= dist
        self.cache_urls[urlid] = data
        return data

    def cos_sim(self, tfidf1, tfidf2):
        '''
        A helper function to compute the cos simliarity between
        news story and centroid.
        @param  data: target news story tfidf vector.
        @type  data: C{dict}
        @param centroid: centroid tfidf vector.
        @type  centroid: C{dict}
        '''
        sim = 0.0
        for key in tfidf1:
            if key in tfidf2:
                word = self.wordids[key]
                a = tfidf1[key]
                b = tfidf2[key]
                sim += a*b
        return sim

    def add_freq_index(self, urlid, wordfreq, categories = []):
        for word in wordfreq:
            self.wordlist.setdefault(word, 0)
            self.wordlist[word] += 1

    def commit_freq_index(self, table):
        self.dftext = {}
        self.wordids = {}
        for word in self.wordlist:
            rowid = self.db.execute("insert into "+table+" (word, dftext) " + \
                "values(%s, %s)", (word, self.wordlist[word]))
            self.wordids[rowid] = word
            self.dftext[word] = (rowid, self.wordlist[word])
        self.wordlist = {}

    def get_article(self, urlid, corpus = False):
        if corpus:
            table = 'cat_corpus'
            cat_table = 'cat_corpus_cats'
        else:
            table = 'urllist'
            cat_table = 'categories'

        row = self.db.selectone("""select u.url, u.title, u.content, u.pubdate,
            u.crawldate, u.processed, u.publisher from %s as u where u.urlid = %s""" % \
            (table, urlid))
        if row != None:
            wordfreq = self.txtpro.simpletextprocess(urlid, row[2])
            processed = False
            if row[5] == 1: processed = True
            categories = []
            cat_rows = self.db.selectall("""select category from %s
                where urlid = %s""" % (cat_table, urlid))
            for cat_row in cat_rows:
                categories.append(cat_row[0])
            return {'urlid': urlid, 'url': row[0], 'title': row[1],
                    'content': row[2], 'pubdate': row[3], 'crawldate': row[4],
                    'processed': processed, 'publisher': row[6],
                    'categories': categories,
                    'wordfreq': wordfreq, 'tfidf': self.get_tfidf(urlid, wordfreq)}
        else:
            return None

    def get_articles_daterange(self, date_start, date_end):
        articles = {}
        rows = self.db.selectall("""select urlid from urllist
            where pubdate >= '%s' and pubdate <= '%s'""" % (date_start, date_end))
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

    def restore_corpus(self):
        self.wordids = {}
        self.dftext = {}
        rows = self.db.selectall("select rowid, word, dftext from wordlist")
        for row in rows:
            self.wordids[row[0]] = row[1]
            self.dftext[row[1]] = (row[0], row[2])
        self.corpus_count = self.db.selectone("select count(*) from cat_corpus")[0]

    def load_corpus(self, ident, pct, debug = False):
        if debug:
            print "Loading corpus..."
        source = ident.split(':')[0]
        name = ident.split(':')[1:]
        if source == "file":
            docs = self.load_file_corpus(name, debug)
        elif source == "db":
            docs = self.load_db_corpus(name, debug)
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

    def load_db_corpus(self, name, debug = False):
        rows = self.db.selectall("""select c.urlid, c.content,
            group_concat(cc.category separator ' ')
            from %s as c, %s as cc
            where c.urlid = cc.urlid
            group by c.urlid order by c.urlid desc""" % (name[0], name[1]))
        print "Processing %d articles..." % len(rows)
        docs = []
        for row in rows:
            wordfreq = self.txtpro.simpletextprocess(row[0], row[1])
            if wordfreq.N() > 0:
                docs.append((row[0], wordfreq, row[2]))
            if debug:
                sys.stdout.write('.')
                sys.stdout.flush()
        return docs

