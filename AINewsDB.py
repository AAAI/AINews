"""
The database wrapper for MySQL. It provides the fundamental functions to
access the MySQL database.
"""

import sys
import re
import MySQLdb

from AINewsConfig import db
           
class AINewsDB:
    def __init__(self):
        host = db['database.host']
        user = db['database.user']
        pwd = db['database.pwd']
        database = db['database.db']
        try:
            self.con = MySQLdb.connect(host = host,
                                        user = user,
                                        passwd = pwd,
                                        db = database,
                                        use_unicode = True)
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit (1)
        self.cursor = self.con.cursor()
    
            
    def __del__(self):
        self.close()
        
    def close(self):
        self.cursor.close()
        self.con.close()
        
    def execute(self, query, args = None):
        """
        Execute SQL query with no return value
        """
        if args == None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, args)
        return self.cursor.lastrowid

    def insert(self, query):
        """
        Execute SQL query and return the last rowid
        """
        self.cursor.execute(query)
        return self.cursor.lastrowid
        
    def selectone(self, query):
        """
        Execute SQL query with only one return value
        """
        self.cursor.execute(query)
        return self.cursor.fetchone()
        
    def selectall(self, query):
        """
        Execute SQL query with multiple return values
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def isindexed(self, url):
        """
        Return true if this url is already indexed/stored in database
        @param url: url of the news
        @type url: C{string}
        """
        url = re.escape(url.encode('utf-8'))
        self.cursor.execute \
            ("select rowid from urllist where url='%s'" % url)
        urlrow = self.cursor.fetchone()
        if urlrow != None:
            # Check if it has actually been crawled
            self.cursor.execute \
                ("select * from textwordurl where urlid = %d" % urlrow[0])
            wordrow = self.cursor.fetchone()
            if wordrow != None: return True
        return False
    
    def geturlid(self, url):
        """
        Given a url, return the urlid from the database. If the url is not
        indexed, return -1.
        @param url: url of the news
        @type url: C{string}
        """
        url = re.escape(url.encode('utf-8'))
        self.cursor.execute \
            ("select rowid from urllist where url='%s'" % url)
        urlrow = self.cursor.fetchone()
        if urlrow != None:
            return urlrow[0]
        else:
            return -1
        
    def deleteurlid(self, urlid):
        """
        Delete from urllist given the urlid.
        @param urlid: urlid of the news
        @type urlid: C{int}
        """
        sql = "delete from urllist where rowid = %d" % urlid
        self.cursor.execute (sql)
    
    def getentryid(self, table, field, value):
        """
        Auxilliary function for either getting the rowid with certain field  
        value or inserting a new row if it's not present.
        """
        value = re.escape(value.encode('utf-8'))
        self.cursor.execute("select rowid from %s where %s='%s'" % \
                             (table, field, value))
        res = self.cursor.fetchone()
        if res == None:
            self.cursor.execute("insert into %s (%s) values ('%s')" % \
                                    (table, field, value))
            return self.cursor.lastrowid    
        else:
            return res[0]
            
    def get_newstext(self, urlid):
        sql = "select title, description from urllist where rowid = %d" % urlid
        return self.selectone(sql)
        
    def get_totaldoc(self):
        totaldoc = self.selectone('select count(*) from urllist')
        return totaldoc[0]
   
