
import unittest
from datetime import date

from AINewsConfig import config, paths
from AINewsDB import AINewsDB
from AINewsCorpus import AINewsCorpus
from AINewsCrawler import AINewsCrawler
from AINewsPublisher import AINewsPublisher

#class TestAINewsCorpus(unittest.TestCase):
#
#    def setUp(self):
#        self.corpus = AINewsCorpus()


class TestAINewsCrawler(unittest.TestCase):

    def setUp(self):
        self.corpus = AINewsCorpus(True)
        self.crawler = AINewsCrawler(True)
        self.publisher = AINewsPublisher(True)
        self.crawler.articles = [{'url': 'http://www.wired.com/wiredenterprise/2013/05/hinton/?utm_source=feedburner&utm_medium=feed&utm_campaign=Feed%3A%20wired/index%20%28Wired%3A%20Top%20Stories%29', 'title': 'aaa aaa aaa aaa', 'pubdate': date.today(), 'source': 'abc', 'source_id': '0', 'source_relevance': 50}]
    
    def test_fetch_all_articles(self):
        self.crawler.fetch_all_articles()
        print self.corpus.get_article(1)
        print self.corpus.get_unprocessed()
        self.publisher.filter_and_process()
        self.publisher.generate_feed_import()
        self.assertEqual(1, 1)


if __name__ == '__main__':
    unittest.main()

