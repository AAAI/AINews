"""
AINewsRanker class is used for weekly news story publishing.
It outputs a pickle file 'output/topnews.pkl' which contains the information of
the final news list. Then, AINewsPublish class will read in this file and
pubulish the news list in different media.

The procedure is as follows:
(1) it collects all candidate AI-Related news during the latest period 
    (by default 7 days) from database;
(2) it AINewsSim class is called to cluster near-duplicated news. Only one
    news closest to the centroid will represent that cluster to be published.
(3) AINewsSVM is used to predict 'interests level' of those candidate news
    by the SVM classifier trained by previously human-rated news stories.
(4) next, news are ordered by:
    a) interests level (SVM classified importance)
    b) its near-duplicated news number (more duplicated news means important)
    c) the importance of the source publisher (NY Times, BBC is more important
       than CNet, Wired)
(5) finally, top 12 news are selected, retrieved its informaton and saved
    into output/topnews.pkl which is ready for publishing.
"""
import math
import time
import re
import types
import os
from datetime import date, timedelta
from operator import itemgetter



from AINewsConfig import config, aitopic_urls, whitelist_unigrams, \
                        whitelist_bigrams, whitelist_trigrams, paths
from AINewsDB import AINewsDB
from AINewsSVM import AINewsSVM
from AINewsSim import AINewsSim
from AINewsTools import loadpickle, unescape,  getwords, savepickle, loadfile2

class AINewsRanker:
    def __init__(self):
        period = int(config['ainews.period'])
        self.begindate = date.today() - timedelta(days = period)
        self.debug = config['ainews.debug']
        
        self.svm = AINewsSVM()
        self.svm.load_news_words()
        
        self.db = AINewsDB()
        
        self.rank_cutoff  = int(config['ranker.rank_cutoff'])
        self.relscores = (float(config['ranker.most_relevent_score']), \
                          float(config['ranker.mild_relevent_score']), \
                          float(config['ranker.no_relevent_score']) )
        self.sim = AINewsSim()
        self.source_order = config['ranker.source_order'].split(':')
        N = len(self.source_order)
        self.srcscores = {}
        for i, src in enumerate(self.source_order):
            self.srcscores[src] = (N-i) * 10
            
        
        self.unigrams = []
        self.bigrams  = []
        self.trigrams = []
        for unigram in whitelist_unigrams:
            wordid = self.get_wordid(unigram)
            if wordid != 0:
                self.unigrams.append(wordid)
        for bigram in whitelist_bigrams:
            terms = bigram.split(' ')
            wordid0 = self.get_wordid(terms[0])
            wordid1 = self.get_wordid(terms[1])
            if wordid0 != 0 and wordid1 != 0:
                self.bigrams.append((wordid0, wordid1))
        for trigram in whitelist_trigrams:
            terms = trigram.split(' ')
            wordid0 = self.get_wordid(terms[0])
            wordid1 = self.get_wordid(terms[1])
            wordid2 = self.get_wordid(terms[2])
            if wordid0 != 0 and wordid1 != 0 and wordid2 != 0:
                self.trigrams.append((wordid0, wordid1, wordid2))
            
    def get_wordid(self, word):
        sql = "select rowid from wordlist where word = '%s'" % word
        row = self.db.selectone(sql)
        if row == None: return 0
        else: return row[0]

    def get_word(self, wordid):
        sql = "select word from wordlist where rowid = %d" % wordid
        row = self.db.selectone(sql)
        if row == None: return ""
        else: return row[0]
        
    def rank(self):
        """
        The key function to rank the candidate news stories.
        @return: a dictionary of key:urlid, value:score.
        @rtype: C{dict}
        """
        # For each url, keep a transcript (string) of various
        # scoring changes made to it
        transcript = {}

        # Get SVM classifier's probability for news candidates
        scores = {}
        candidate_urlids = self.get_candidates()
        
        ################################################    
        #
        # Remove redundancy news by measure similarity via AINewsSim
        #
        ################################################
        sim_cutoff = float(config['sim.cutoff'])
        (centroid_ids, nodup_ids, simnews) = self.sim.detect_duplicates(candidate_urlids, sim_cutoff)
        urlids = centroid_ids + nodup_ids
        #########################################
        #
        #       SVM score
        #
        #########################################
        # Change the probability into score.
        rows = self.svm.predict_probability_all(urlids)
        for (i,row) in enumerate(rows):
            urlid = row[0]
            transcript[urlid] = []

            rs = self.relscores[2]
            if row[1] > row[2]:
                if row[1] > row[3]:
                    rs = self.relscores[0]
                    scores[urlid] = rs * 10000
                    transcript[urlid].append("Relevance score is 'most relevant'")
                    transcript[urlid].append( \
                        "Starting score at config'd relevance score %.1f * 10000 = %.1f" % \
                        (rs, scores[urlid]))
                    if urlid in simnews.keys():
                        scores[urlid]+= len(simnews[urlid])*10
                        transcript[urlid].append( \
                            "Added 10*%d to score because %d stories are similar = %.1f" % \
                            (len(simnews[urlid]), len(simnews[urlid]), scores[urlid]))
            elif row[2] > row[3]:
                rs = self.relscores[1]
                scores[urlid] = rs * 10000
                transcript[urlid].append("Relevance score is 'mildly relevant'")
                transcript[urlid].append( \
                    "Starting score at config'd relevance score %.1f * 10000 = %.1f" % \
                    (rs, scores[urlid]))
                if urlid in simnews.keys():
                    scores[urlid]+= len(simnews[urlid])*10
                    transcript[urlid].append( \
                        "Added 10*%d to score because %d stories are similar = %.1f" % \
                        (len(simnews[urlid]), len(simnews[urlid]), scores[urlid]))

            sql = "UPDATE urllist SET svmscore = %f WHERE rowid = %d" \
                    % (rs, urlid)
            self.db.execute(sql)

            # update initial SVM score
            sql = """UPDATE urllist SET initsvm = %f
                     WHERE rowid = %d and isnull(initsvm)""" % (rs, urlid)
            self.db.execute(sql)

        '''
        # Update finalscore of each news in urllist table
        for urlid in scores.keys():
            sql = "UPDATE urllist SET finalscore = %f WHERE rowid = %d" \
                    % (scores[urlid], urlid)
            self.db.execute(sql)
        '''
        for urlid in scores.keys():
            words = self.count_whitelist(urlid)
            cnt = sum(words.values())
            scores[urlid] += cnt * 100
            wordlist = []
            for w in words.keys():
                wordlist.append("'%s': %d" % (w, words[w]))
            transcript[urlid].append("Whitelist occurrences: %s" % ", ".join(wordlist))
            transcript[urlid].append( \
                "Adding %d*100 to score due to %d total occurrences of whitelist words = %.1f" % \
                (cnt, cnt, scores[urlid]))
       
        
        # rank by publisher source
        for urlid in scores.keys():
            pub_src = self.get_publisher(urlid)
            if pub_src in self.srcscores.keys():
                scores[urlid] += self.srcscores[pub_src]
                transcript[urlid].append("Adding to score publisher's importance (+%d, position %d/%d in the list) = %.1f" % \
                    (self.srcscores[pub_src], self.source_order.index(pub_src), \
                     len(self.source_order), scores[urlid]))
            else:
                scores[urlid] += len(self.srcscores.keys())*5 # *10/2
                transcript[urlid].append( \
                    "Adding to score standard (minor) publisher's importance score (%d) = %.1f" % \
                    (len(self.srcscores.keys())*5, scores[urlid]))
        
        
        # output into pkl file which is ready for publishing.
        sscores = sorted(scores.iteritems(), key=itemgetter(1), reverse=True)
        topnews = []
        for (urlid, score) in sscores[:self.rank_cutoff]:
            info = self.get_urlinfo(urlid)
            info['score'] = score
            info['transcript'] = transcript[urlid]
            topnews.append(info)
        savepickle(paths['ainews.output'] + "topnews.pkl", topnews)
    
    
        
    def get_candidates(self):
        """
        Get all news candidates during the candidate period.
        @return: a list of candidate news' urlid
        @rtype: C{list}
        """
        sql = """select rowid from urllist where pubdate >= '%s' and topic <> 'NotRelated'
                 order by rowid asc""" % self.begindate
        rows = self.db.selectall(sql)
        urlids = [row[0] for row in rows]
        return urlids
        
    def get_match_rows(self, querywords):
        """
        Get the candidate news whose content contains certain query words
        @param querywords:  get the candidate news who contains the query words.
        @type querywords: C{string}
        """
        # Strings to build the query
        fieldlist = 'w0.urlid'
        texttablelist = ''
        clauselist = ''
        wordids = []
        
        # Split the words by spaces
        words = getwords(querywords)
        tablenumber = 0
        
        for word in words:
            # Get the word ID
            wordrow = self.db.selectone(
                        "select rowid from wordlist where word = '%s'" % word)
            
            if wordrow != None:
                wordid = wordrow[0]
                wordids.append(wordid)
                if tablenumber > 0:
                    texttablelist += ','
                    clauselist += ' and w%d.urlid = w%d.urlid and ' % \
                                  (tablenumber-1, tablenumber)
                fieldlist += ',w%d.freq' % tablenumber
                texttablelist += 'textwordurl w%d' % tablenumber
                clauselist += 'w%d.wordid = %d' % (tablenumber, wordid)
                tablenumber += 1
            # if any query word has not been indexed and stored
            else:  return [], []
    
        # Only retrieve latest news in period
        texttablelist  += ', urllist'
        clauselist     += """ and w0.urlid = urllist.rowid
                        and urllist.pubdate >= '%s'
                        and urllist.topic <> 'NotRelated'""" % self.begindate
        # Create the query from the separate parts
        textfullquery = 'select %s from %s where %s' % \
                            (fieldlist, texttablelist, clauselist)
        
        text_rows = self.db.selectall(textfullquery)
        return text_rows, wordids
    
    def get_urlinfo(self, urlid):
        """
        Get url news  information given the urlid
        @param urlid: urlid 
        @type urlid: C{int}
        """
        sql = """select url, pubdate, crawldate, title, publisher, topic, description,
                        initsvm, svmscore, rate, adminrate, ratesd, ratecount
                from urllist where rowid = %d""" % urlid
        row = self.db.selectone(sql)
        if row[6] == None:
            desc_file = paths['ainews.news_data'] + 'desc/'+str(urlid)+'.pkl'
            desc = loadpickle(desc_file).strip()
        else:
            desc = unescape(row[6])
        meta_file = paths['ainews.news_data'] + 'meta/'+str(urlid)+'.pkl'
        meta = []
        if os.path.exists(meta_file):
            meta = loadpickle(meta_file)
        topicsims = {}
        if len(meta) > 4: topicsims = meta[4]
        print str(urlid) + ":" + str(topicsims)

        if isinstance(desc, types.StringType):
            desc = unicode(desc, errors = 'ignore')
        url = unescape(row[0])
        newsinfo = {'urlid': urlid, 'url': url, 'pubdate': row[1], 'crawldate': row[2],
                'title': row[3], 'publisher': row[4], 'topic': row[5],
                'desc': desc, 'initsvm': row[7], 'svmscore': row[8],
                'rate': row[9], 'adminrate': row[10], 'ratesd': row[11],
                'ratecount': row[12], 'topicsims': topicsims}
        return newsinfo
    
    def get_publisher(self, urlid):
        """
        Get publisher/news source for score adjusting and similarity ranking
        @param urlid: urlid 
        @type urlid: C{int}
        """
        sql = """select publisher from urllist where rowid = %d""" % urlid
        row = self.db.selectone(sql)
        return row[0]
        
    ## TODO: This is broken; bigrams and trigrams aren't counted properly;
    ## the bigram "hello world" need not occur together (as a bigram) in
    ## order for this function count it (count will be min occurrence of
    ## hello and world, independently)
    def count_whitelist(self, urlid):
        sql = "select wordid, freq from textwordurl where urlid = %d" % urlid
        rows = self.db.selectall(sql)
        data = {}
        for row in rows:
            data[row[0]] = int(row[1])
        
        words = {}
        for unigram in self.unigrams:
            word = self.get_word(unigram)
            if unigram in data.keys():
                words[word] = data[unigram]
        for bigram in self.bigrams:
            word = self.get_word(bigram[0]) + " " + self.get_word(bigram[1])
            if bigram[0] in data.keys() and bigram[1] in data.keys():
                words[word] = min(data[bigram[0]], data[bigram[1]])
        for trigram in self.trigrams:
            word = self.get_word(trigram[0]) + " " + self.get_word(trigram[1]) + \
                " " + self.get_word(trigram[2])
            if trigram[0] in data.keys() and trigram[1] in data.keys() \
               and trigram[2] in data.keys():
                words[word] = min(data[trigram[0]], data[trigram[1]], data[trigram[2]])
        return words
                
  
