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
from datetime import date, timedelta
from operator import itemgetter



from AINewsConfig import config, aitopic_urls, whitelist_unigrams, \
                        whitelist_bigrams, whitelist_trigrams
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
        source_order = config['ranker.source_order'].split(':')
        N = len(source_order)
        self.srcscores = {}
        for i, src in enumerate(source_order):
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
        
    def rank(self):
        """
        The key function to rank the candidate news stories.
        @return: a dictionary of key:urlid, value:score.
        @rtype: C{dict}
        """
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

	    rs = self.relscores[2]
	    if row[1] > row[2]:
                if row[1] > row[3]:
		    rs = self.relscores[0]
		    scores[urlid] = rs * 10000
		    if urlid in simnews.keys():
			scores[urlid]+= len(simnews[urlid])*10
            elif row[2] > row[3]:
		rs = self.relscores[1]
		scores[urlid] = rs * 10000
		if urlid in simnews.keys():
			scores[urlid]+= len(simnews[urlid])*10

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
            scores[urlid] += self.count_whitelist(urlid) * 100 
       
        
        # rank by publisher source
        for urlid in scores.keys():
            pub_src = self.get_publisher(urlid)
            if pub_src in self.srcscores.keys():
                scores[urlid] += self.srcscores[pub_src]
            else:
                scores[urlid] += len(self.srcscores.keys())*5 # *10/2
        
	
        # output into pkl file which is ready for publishing.
        sscores = sorted(scores.iteritems(), key=itemgetter(1), reverse=True)
        topnews = []
        for (urlid, score) in sscores[:self.rank_cutoff]:
            info = self.get_urlinfo(urlid)
            info['score'] = score
            topnews.append(info)
        savepickle("output/topnews.pkl", topnews)
    
    
        
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
        sql = """select url, pubdate, title, publisher, topic, description
                from urllist where rowid = %d""" % urlid
        row = self.db.selectone(sql)
        if row[5] == None:
            desc_file = 'news/desc/'+str(urlid)+'.pkl'
            desc = loadpickle(desc_file).strip()
        else:
            desc = unescape(row[5])
        if isinstance(desc, types.StringType):
            desc = unicode(desc, errors = 'ignore')
        url = unescape(row[0])
        newsinfo = {'urlid': urlid, 'url' : url, 'pubdate' : row[1], 
                'title' : row[2], 'publisher' : row[3], 'topic': row[4],
                'desc': desc}
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
        
    def count_whitelist(self, urlid):
        sql = "select wordid, freq from textwordurl where urlid = %d" % urlid
        rows = self.db.selectall(sql)
        data = {}
        for row in rows:
            data[row[0]] = int(row[1])
        
        cnt = 0
        for unigram in self.unigrams:
            if unigram in data.keys():
                cnt += data[unigram]
        for bigram in self.bigrams:
            if bigram[0] in data.keys() and bigram[1] in data.keys():
                cnt += min(data[bigram[0]], data[bigram[1]])
        for trigram in self.trigrams:
            if trigram[0] in data.keys() and trigram[1] in data.keys() \
               and trigram[2] in data.keys():
                cnt += min(data[trigram[0]], data[trigram[1]], data[trigram[2]])
        return cnt
                
  