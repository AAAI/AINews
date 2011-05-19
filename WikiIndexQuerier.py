"""
WikiIndexQuerier takes in a text document as input, and query the Lucene indexed
3.1M wikipedia abstract documents. 

"""
from lucene import \
    QueryParser, IndexSearcher, StandardAnalyzer, SimpleFSDirectory, File, \
    VERSION, initVM, Version, HashSet, Term, ScoreDoc
from AnalyzerUtils import AnalyzerUtils

from nltk.corpus.reader.wordnet import Synset
from operator import itemgetter
from types import StringType, ListType
from AINewsDB import AINewsDB
from WikiAnalyzerUtils import WikiAnalyzerUtils
class WikiIndexQuerier():
    def __init__(self, index_dir, debug = False):
        self.debug = debug
        self.version = 'lucene' + VERSION
        initVM()
        directory = SimpleFSDirectory(File(index_dir))
        self.searcher = IndexSearcher(directory, True)
        self.analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
        self.numDocs = self.searcher.getIndexReader().numDocs()
        self.db = AINewsDB()
        
    def __del__(self):
        self.searcher.close()
        
    def query(self, rawtext, N):
        tokens = WikiAnalyzerUtils.extractTokens(self.analyzer, rawtext)
        text = ' OR '.join(["(topic:"+token+" OR "+"abstract:"+token+")" for token in tokens])
        queryparser = QueryParser(Version.LUCENE_CURRENT, "", self.analyzer)
        queryparser.setDefaultOperator(QueryParser.Operator.OR)
        query = queryparser.parse(text)
        hits = self.searcher.search(query, N)
        scoreDocs = hits.scoreDocs
        res = {}
        for scoreDoc in scoreDocs:
            doc = self.searcher.doc(scoreDoc.doc)
            res[(doc["id"], doc["topic"])] = scoreDoc.score
        return res
    
    """    
    def query(self, text, N):
        query = QueryParser(Version.LUCENE_CURRENT, 'abstract',
                            self.analyzer).parse(text)
        ########################################################
        #   terms = HashSet()
        #   terms.add(":House")
        #   query.extractTerms(terms)
        #   print "list query terms:", type(terms), terms
        ######################################################## 
        hits = self.searcher.search(query, N)
        scoreDocs = hits.scoreDocs
        print "Total matched documents:", hits.totalHits
        res = {}
        if(self.debug):
            for scoreDoc in scoreDocs:
                doc = self.searcher.doc(scoreDoc.doc)
                explanation = self.searcher.explain(query, scoreDoc.doc)
                print 'topic:', doc.get("topic  ")
                arr = explanation.getDetails()
                print '\t', explanation, arr[0].value, arr[1].value
        for scoreDoc in scoreDocs:
            print   scoreDoc
            doc = self.searcher.doc(scoreDoc.doc)
            #res[(doc["id"],doc["topic"])] = scoreDoc.score
            res[doc["id"]] = scoreDoc.score 
        return res
    """
##########################################
#
#      Testing
#
##########################################
def print_results(results):
    items = sorted( results.items(), key=itemgetter(1), reverse=True)
    for item in items:
        print item
        
if __name__ == "__main__":
    INDEX_DIR =  "lucene/wiki"
    querier = WikiIndexQuerier(INDEX_DIR, debug = False)
    analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
    while True:
        print
        print "Hit enter with no input to quit."
        rawtext = raw_input("Query:")
        if rawtext != "":
            wikidocs = querier.query(rawtext, 20)
            for doc in wikidocs:
                print doc
        else:
            break
    
        
__all__ = [ 
    'WikiIndexQuerier'
    ]