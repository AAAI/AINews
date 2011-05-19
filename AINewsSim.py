"""
The purpose of AINewsSim is to remove similar/duplicated news on the same event.
AINewsSim is used to measure the similarity between any two news stories, given
their news urlids and return the similarity value between 0 to 1.

AINewsSim also cluster all the similar news into one cluster. Then, it computes
the centroid of the cluster and select the news closest to the cluster to
represent the cluster.

Near-duplicated news clustering is the first processing during Ranking.
"""

import math
from datetime import date, timedelta

from AINewsDB import AINewsDB
from AINewsConfig import config
from AINewsTools import unescape

def sortbysize(set1, set2):
    return len(set2)-len(set1)

class AINewsSim:
    """
    TFIDF for each news story is measured and are used to measure the similarity
    value. For all the similar news story, they are collected in one group.
    For each group, it measures the news's source/publisher and scores and only
    keep the highest score news in that group. The rest news in the same group
    are discarded.
    """
    def __init__(self, near = 3, far = 140):
        self.db = AINewsDB()
        totaldoc = self.db.selectone('select count(*) from urllist')
        self.logD = math.log(totaldoc[0] + 1, 2)
        self.tfidfs = {}
        self.dates = {}
        self.cluster = []
        self.cluster_centroid = []
        self.near = near
        self.far = far
        self.dupids = set()
        self.simnews = {}
     
    def detect_duplicates(self, urlids, sim_cutoff):
        '''
        Key function called by AINewsRanker.
        It recieves a list of urlids and similarity cutoff as input.
        Then, it clusters all urlids based on the cutoff.
        Next, it computes each cluster's centroid as well as the news closest
        to the centroid.
        Finally, it combines the clustering result with those individual news
        as output for AINewsRanker
        '''        
        # Clustering
        N = len(urlids)
        for i in range(N):
            for j in range(i+1, N):
                val = self.sim(urlids[i], urlids[j])
                val *= self.temporal_coefficient(urlids[i],urlids[j])
                if val >= sim_cutoff:
                    self.add_link(urlids[i],urlids[j])
                    
        # Compute centroid
        self.centroid()
        
        # Output for AINewsRanker
        no_dupids = []
        for urlid in urlids:
            if urlid not in self.dupids:
                no_dupids.append(urlid)
        return self.cluster_centroid, no_dupids, self.simnews
        
        
    def sim(self, docid1, docid2):
        """
        Compute the similarity value between two story documents.
        """
        doc1 = self.get_tfidf(docid1)
        doc2 = self.get_tfidf(docid2)
        simval = 0.0
        for wordid in doc1.keys():
            if wordid in doc2.keys():
                simval += doc1[wordid] * doc2[wordid]
        return simval
    
    def set_temporal(self, near, far):
        """
        Setting the temporal function's parameters for computing
        temporal coefficient.
        """
        self.near = near
        self.far = far
    
    def temporal_coefficient(self, docid1, docid2):
        """
        Measure the temporal weight coefficient by multiplying on the simval.
        To reduce the simval if two news pub-dates are far apart.
        """
        date1 = self.dates[docid1]
        date2 = self.dates[docid2]
        datedelta = math.fabs((date2-date1).days)
            
        if datedelta <= self.near:
            return 1.0
        elif datedelta >= self.far:
            return 0.0
        else:
            #return 1.0*(self.far-datedelta)/(self.far-self.near)
            return 0.5*math.cos((datedelta-self.near)*math.pi/(self.far-self.near))+0.5
        

    def get_tfidf(self, urlid):
        """
        Measure the tfidf value of the bag of words for each story.
        @param urlid: urlid of the news story
        @type urlid: C{int}
        """
        if urlid in self.tfidfs.keys():
            return self.tfidfs[urlid]
        
        doc = {}
        sql = "select t.wordid, t.freq, w.dftext from textwordurl as t,\
                wordlist as w where t.urlid = %d and t.wordid = w.rowid" % urlid
        rows = self.db.selectall(sql)
        sqsum = 0.0
        for row in rows:
            
            val = math.log(row[1] + 1, 2) * (self.logD - math.log(row[2]+1, 2))
            #val = row[1] * (self.logD - math.log(row[2]+1, 2))
            doc[row[0]] = val
            sqsum += val * val
        dist = math.sqrt(sqsum)
        for key in doc.keys():
            doc[key] /= dist
            
        self.tfidfs[urlid] = doc
        
        # Search and cache date
        sql = "select pubdate from urllist where rowid = '%s'" % (urlid)
        row = self.db.selectone(sql)
        self.dates[urlid] = row[0]                  # object type datetime.date
        
        return doc
    
    def add_link(self, i, j):
        """
        All similar news stories are clustered in corresponding set. This
        function add two stories into the cluster. If any one of the story
        has already exists, both of them are added into the existing set.
        Otherwise, they are added as a new set.
        @param i: urlid of one similar news story
        @type i: C{int}
        @param j: urlid of another similar news story
        @type j: C{int}
        """
        self.dupids.add(i)
        self.dupids.add(j)
        for c in self.cluster:
            for id in c:
                if id == i:
                    c.add(j)
                    return
                if id == j:
                    c.add(i)
                    return
        self.cluster.append(set([i,j]))
    
    
        
    def centroid(self):
        '''
        It computes the centroid of each clustered news. 
        Then, it finds the news closest to the centroid of each cluster;
        record that news to represent that cluster.
        '''
        self.cluster.sort(cmp=sortbysize)
        for c in self.cluster:
            centroid = {}
            for urlid in c:
                doc = self.get_tfidf(urlid)
                for key in doc.keys():
                    centroid.setdefault(key, 0)
                    centroid[key] += doc[key]
            # Average to get centroid            
            N = len(c)
            distsq = 0.0
            for key in centroid.keys():
                val = centroid[key]/N
                centroid[key] = val
                distsq += val * val
            dist = math.sqrt(distsq)
            for key in centroid.keys():
                centroid[key] /= dist
            
            # Find the closest urlid to centroid
            max_id = 0
            max_sim = 0
            for urlid in c: 
                csim = self.sim_centroid(centroid, urlid)
                if csim >= max_sim:
                    max_sim = csim
                    max_id = urlid
            self.cluster_centroid.append(max_id)
            self.simnews[max_id] = c
   

            
    def sim_centroid(self, centroid, urlid):
        '''
        Compute the similarity between a news and a centroid of that cluster.
        '''
        doc = self.get_tfidf(urlid)
        simval = 0.0
        for wordid in doc.keys():
            simval += centroid[wordid] * doc[wordid]
        return simval
            
