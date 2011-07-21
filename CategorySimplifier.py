
import random
from AINewsDB import AINewsDB

db = AINewsDB()

db.execute('delete from cat_corpus_cats_single')

urlids = []
rows = db.selectall('select urlid from cat_corpus')
for row in rows:
    urlids.append(row[0])

for urlid in urlids:
    cats = []
    rows = db.selectall('select category from cat_corpus_cats where urlid = %d' % \
            urlid)
    for row in rows:
        cats.append(row[0])
    
    # choose random single category, update database
    #random.shuffle(cats)
    
    db.execute("insert into cat_corpus_cats_single values(%d, '%s')" % \
            (urlid, cats[0]))


