
import unittest
from datetime import date

from AINewsConfig import config, paths
from AINewsDB import AINewsDB
from AINewsCorpus import AINewsCorpus
from AINewsCrawler import AINewsCrawler

#class TestAINewsCorpus(unittest.TestCase):
#
#    def setUp(self):
#        self.corpus = AINewsCorpus()


class TestAINewsCrawler(unittest.TestCase):

    def setUp(self):
        self.corpus = AINewsCorpus(True)
        self.crawler = AINewsCrawler(True)
        self.crawler.articles = [{'url': 'http://www.vancouversun.com/technology/personal-tech/Video+Google+Glass+forefront+wearable+technology/8402234/story.html', 'title': 'xyz', 'pubdate': date.today(), 'source': 'abc', 'source_id': '0', 'source_relevance': 50}]
    
    def test_fetch_all_articles(self):
        self.crawler.fetch_all_articles()
        print self.corpus.get_article(1)
        self.assertEqual(1, 1)


if __name__ == '__main__':
    unittest.main()

