"""
AINewsRemover is used to remove the crawled news in the database. The crawled
news data includes the url infomation, the words of the news, decrement the
document freq of the words, and the rater's log of the news.

Since AINewsCrawler will skip crawled news, it is hard to testing the
crawler algorithm. Thus, remover is used to remove those crawled news so that
the crawler can crawl them again.
       
"""
import os
import sys
from datetime import date, timedelta
from AINewsDB import AINewsDB
from AINewsConfig import config

class AINewsRemover():
    def __init__(self):
        self.db = AINewsDB()
        self.today = date.today()
        #self.logpath = "../pub/rater/logs/"
        
    def remove_by_urlid(self, urlid):
        """
        Given a urlid, remove database info and rater logs of the urlid
        @param urlid: the target urlid news to be removed
        @type urlid: C{int}
        """
        # Remove word doc freq        
        sql = "DELETE FROM wordlist WHERE dftext = 1 AND rowid in\
                (SELECT wordid FROM textwordurl WHERE urlid = %d)" % urlid
        self.db.execute(sql)
        sql = "UPDATE wordlist SET dftext = dftext - 1 WHERE rowid in\
                (SELECT wordid FROM textwordurl WHERE urlid = %d)" % urlid
        self.db.execute(sql)
        # Remove word freq
        sql = "DELETE FROM textwordurl WHERE urlid = %d" % urlid
        self.db.execute(sql)
        # Remove url info
        sql = "DELETE FROM urllist WHERE rowid = %d" % urlid
        self.db.execute(sql)
        # Remove rating logs
        #logfile = self.logpath + str(urlid) + ".rating"
        #if os.path.exists(logfile):
        #    os.remove(logfile)
            
    def remove_by_period(self, period):
        """
        Remove a set of news during this period from today.
        @param period: the # of days to be removed
        @type period: C{int}
        """
        begindate = self.today - timedelta(days = period)
        sql = "SELECT rowid FROM urllist WHERE pubdate >= '%s'" % begindate
        rows = self.db.selectall(sql)
        for row in rows:
            urlid = row[0]
            self.remove_by_urlid(urlid)

if __name__ == "__main__":
    '''
    period = 14
    if len(sys.argv) == 2 and int(sys.argv[1]) > 0:
        period = int(sys.argv[1])
    '''
    remover = AINewsRemover()
    #remover.remove_by_period(period)
    remover.remove_by_urlid(int(sys.argv[1]))
