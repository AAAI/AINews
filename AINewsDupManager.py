"""
AINews Duplicated News Manager.
It maintains the ainews.dup/dupurl tables in the MySQL database which performs 
as human rated experimental dataset. It used for compute the recall/precision
rate of perform duplicate news removal task.

"""

from AINewsDB import AINewsDB

class AINewsDupManager():
    def __init__(self):
        self.db = AINewsDB()
        
    def get_dupid(self, urlid):
        sql = "select dupid from dupurl where urlid = %d" % urlid
        return self.db.selectone(sql)
    
    def get_urlids(self, dupid):
        sql = "select urlid from dupurl where dupid = %d" % dupid
        rows = self.db.selectall(sql)
        return [row[0] for row in rows]
        
    def find_dup(self, urlid):
        dupid = self.get_dupid(urlid)
        return self.get_urlids(dupid)
    
    def create_dupset(self, urlids, centroid, comment=""):
        sql = "select dupid from dup where centroid = '%s'" % centroid
        res = self.db.selectone(sql)
        if res!= None: return
        sql = "insert into dup(centroid, comment) values ('%s', '%s') " \
              % (centroid, comment)
        dupid = self.db.insert(sql)
        self.add_dup(dupid, urlids)
        
    def add_dup(self, dupid, urlids):
        for urlid in urlids:
            sql = "insert into dupurl(dupid, urlid) values ('%s', '%s')" % \
                  (dupid, urlid)
            self.db.insert(sql)
            
    def delete_dupset(self, dupid):
        sql = "delete from dupurl where dupid = %d" % dupid
        self.db.execute(sql)
        sql = "delete from dup where dupid = %d" % dupid
        self.db.execute(sql)
       
##########################################
#
#      Testing
#
##########################################

if __name__ == "__main__":
    dupmng = AINewsDupManager()
    #dupmng.create_dupset([111,122,134], 122)
    #print dupmng.find_dup(134)
   