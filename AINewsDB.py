# This file is part of NewsFinder.
# https://github.com/joshuaeckroth/AINews
#
# Copyright (c) 2011 by the Association for the Advancement of
# Artificial Intelligence. This program and parts of it may be used and
# distributed without charge for non-commercial purposes as long as this
# notice is included.

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
                                        charset = 'utf8',
                                        use_unicode = True,
                                        connect_timeout = 120)
            self.con.autocommit(True)
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

    def selectone(self, query, args = None):
        """
        Execute SQL query with only one return value
        """
        self.execute(query, args)
        return self.cursor.fetchone()
        
    def selectall(self, query, args = None):
        """
        Execute SQL query with multiple return values
        """
        self.execute(query, args)
        return self.cursor.fetchall()
    
    def crawled(self, url):
        urlrow = self.selectone("select url from crawled where url=%s", (url,))
        return (urlrow != None)

    def set_crawled(self, url):
        self.execute("insert into crawled (url) values (%s)", (url,))


