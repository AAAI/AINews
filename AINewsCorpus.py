
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
        
        self.tfijk = {}
        self.tfik = {}
        self.csd = {}
        for cat in self.categories:
            self.tfik[cat] = {}
            self.tfijk[cat] = {}
            self.csd[cat] = {}
        self.icsd = {}
        self.sd = {}
        self.cat_urlids = {}

        self.icsd_pow = 0.0
        self.csd_pow = 0.0
        self.sd_pow = 0.0

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

    def get_icsd(self, word):
        if word in self.icsd:
            return self.icsd[word]
        self.icsd[word] = 0.0
        for cat in self.categories:
            tmp = self.tfik[cat][word]
            for cat2 in self.categories:
                tmp -= (self.tfik[cat2][word] / float(len(self.categories)))
            tmp = tmp*tmp
            self.icsd[word] += tmp / float(len(self.categories))
        self.icsd[word] = math.sqrt(self.icsd[word])
        return self.icsd[word]

    def get_csd(self, cat, word):
        if cat in self.csd:
            if word in self.csd[cat]:
                return self.csd[cat][word]
        else:
            self.csd[cat] = {}

        self.csd[cat][word] = 0.0
        for urlid in self.cat_urlids[cat]:
            if word in self.tfijk[cat][urlid]:
                tmp = self.tfijk[cat][urlid][word] - self.tfik[cat][word]
            else:
                tmp = 0 - self.tfik[cat][word]
            self.csd[cat][word] += tmp*tmp / float(len(self.cat_urlids[cat]))
        self.csd[cat][word] = math.sqrt(self.csd[cat][word])
        return self.csd[cat][word]

    def get_sd(self, word):
        if word in self.sd:
            return self.sd[word]

        sub = 0.0
        for cat in self.categories:
            for urlid in self.tfijk[cat]:
                if word in self.tfijk[cat][urlid]:
                    sub += float(self.tfijk[cat][urlid][word]) / self.cat_totals
        self.sd[word] = 0.0
        for cat in self.categories:
            for urlid in self.tfijk[cat]:
                if word in self.tfijk[cat][urlid]:
                    tmp = self.tfijk[cat][urlid][word] - sub
                else:
                    tmp = 0 - sub
                self.sd[word] += tmp*tmp / self.cat_totals
        self.sd[word] = math.sqrt(self.sd[word])
        return self.sd[word]

    def sim(self, doc1, doc2, category = None):
        return self.cos_sim(self.get_tfidf(doc1[0], doc1[1]), \
            self.get_tfidf(doc2[0], doc2[1]), category)

    def cos_sim(self, tfidf1, tfidf2, category = None):
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
                tdf = math.pow(self.get_icsd(word), self.icsd_pow) * \
                        math.pow(self.get_sd(word), self.sd_pow)
                if category != None and self.get_csd(category, word) != 0.0:
                    tdf *= math.pow(self.get_csd(category, word), self.csd_pow)
                sim += a*b*tdf
        return sim

    def add_freq_index(self, urlid, wordfreq, categories = []):
        for cat in categories:
            if cat in self.categories:
                self.tfijk[cat][urlid] = {}
        for word in wordfreq:
            self.wordlist.setdefault(word, 0)
            self.wordlist[word] += 1

            for cat in categories:
                if cat in self.categories:
                    self.tfijk[cat][urlid].setdefault(word, 0)
                    self.tfijk[cat][urlid][word] += wordfreq[word]

            for cat in self.categories:
                self.tfik[cat].setdefault(word, 0)
            for cat in categories:
                if cat in self.categories:
                    self.tfik[cat][word] += wordfreq[word]

    def commit_freq_index(self, table):
        # calculate tfik
        for cat in self.categories:
            for word in self.tfik[cat]:
                if len(self.cat_urlids[cat]) > 0:
                    self.tfik[cat][word] /= float(len(self.cat_urlids[cat]))

        self.cat_totals = 0.0
        for cat in self.categories:
            self.cat_totals += float(len(self.cat_urlids[cat]))

        self.icsd = {}
        self.csd = {}
        self.sd = {}

        self.dftext = {}
        self.wordids = {}
        for word in self.wordlist:
            rowid = self.db.execute("insert into "+table+" (word, dftext) " + \
                "values(%s, %s)", (word, self.wordlist[word]))
            self.wordids[rowid] = word
            self.dftext[word] = (rowid, self.wordlist[word])
        self.wordlist = {}

    def get_article(self, urlid):
        # try fetching article from urllist table plus text pickle file
        row = self.db.selectone("""select c.title, c.topic, c.pubdate
            from urllist as c where c.rowid = %s and c.topic != 'NotRelated'
            order by c.rowid desc""" % urlid)
        if row != None:
            try:
                content = loadpickle(paths['ainews.news_data'] + \
                        "text/"+str(urlid)+".pkl")
            except: return None
            wordfreq = self.txtpro.simpletextprocess(urlid, content)
            return {'urlid': urlid, 'content': content,
                    'title': row[0], 'wordfreq': wordfreq, \
                    'topics': [row[1]], 'pubdate': row[2]}
        else:
            # try fetching article from cat_corpus
            row = self.db.selectone("""select c.content, c.title,
                group_concat(cc.category separator ' ')
                from cat_corpus as c, cat_corpus_cats as cc
                where c.urlid = %s and c.urlid = cc.urlid
                and cc.category != 'NotRelated'
                group by c.urlid order by c.urlid desc""" % urlid)
            if row != None:
                wordfreq = self.txtpro.simpletextprocess(urlid, row[0])
                return {'urlid': urlid, 'content': row[0],
                        'title': row[1], 'wordfreq': wordfreq, \
                        'topics': row[2].split(' '), 'pubdate': None}
            else:
                return None

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
        self.tfijk = {}
        self.tfik = {}
        for cat in self.categories:
            self.tfik[cat] = {}
            self.tfijk[cat] = {}
        self.cat_urlids = {}
        for cat in self.categories:
            self.cat_urlids[cat] = []
        for c in train_corpus:
            for cat in c[2].split(' '):
                if cat in self.categories:
                    self.cat_urlids[cat].append(c[0])

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
            where c.urlid = cc.urlid and cc.category != 'NotRelated'
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

