"""
AINewsTopic pre-process the 21 AITopics text. The processed bag of words for
each topic is stored and will be used to compare the similarity for
categorizing incoming news.

AINewsCrawler calls AINewsTopic because
AINewsTopic is a pre-processor. It is not used in daily crawling, its output
file is used for similarity comparison.

Feature extraction algorithm NNF can be used to extract the features which
can accelerate the running speed for topic/category detection.
"""
import  math
from AINewsTools import loadfile, loadpickle, savepickle
from AINewsConfig import config, aitopic_urls

class AINewsTopic:
    """
    AINewsTopic is used to assign each newly crawled news story a topic
    based on 21 AITopics.
    """
    def __init__(self):
        """
        Initialize AINewsTopic class
        """
        self.topic_tfidf = loadpickle("topic/topic_tfidf.pkl")
        self.idf = loadpickle("topic/idf.pkl")
        
    def build_topic_tfidf(self):
        '''
        Text Pre-Processing AITopicURL documents for news topic detection.
        '''
        from AINewsTextProcessor import AINewsTextProcessor
        textprocessor = AINewsTextProcessor()
        topics= {}
        
        for url in aitopic_urls:
            topic = url.split('/')[-1]
            print "Processing", topic
            
            lines = loadfile('topic/corpus/'+topic)
            text = ' '.join(lines)
            text_words = textprocessor.simpletextprocess(text)
            
            tfidf = {}
            dist = 0
            for word in text_words:
                if word in self.idf.keys():
                    weight = math.log(1+text_words[word], 2) * self.idf[word]
                    tfidf[word] = weight
                    dist += weight * weight
            dist = math.sqrt(dist)
            if dist != 0:
                for word in tfidf.keys():
                    tfidf[word] = tfidf[word] / dist
                    
            topics[topic] = tfidf
        
        savepickle('topic/topic_tfidf.pkl', topics)
    
    def build_idf(self):
        """
        Using Previous 2008 work: the extracted doc freq to measure 
        the log(idf) and store the values into a file.
        """
        from AINewsTextProcessor import AINewsTextProcessor
        textprocessor = AINewsTextProcessor()
        total = 1616.0
        idf = {}
        lines = loadfile("topic/df_total1616.txt")
        text = " ".join(lines)
        tuples = text.split('[')
        for tuple in tuples:
            elems = tuple.split(' ')
            if len(elems)>=3:
                word = elems[0][:-1]
                freq = int(elems[2])
                mword = textprocessor.simple_pos_morphy(word)
                if mword in idf.keys():
                    idf[mword] += freq
                else:
                    idf[mword] = freq
        
        for key in idf.keys():
            idf[key] = math.log(total / idf[key], 2)
        
        savepickle('topic/idf.pkl', idf)
        
    def find_topic(self, wordfreq):
        """
        Given the wordfreq (a FreqDist object), measure its topic based on
        the similarity between the 21 AITopic's page.
        @param wordfreq: the word freqency of the bag of words of the news.
        @type wordfreq: C{nltk.FreqDist}
        """
        self.target_tfidf = self.__normalize_wordfreq(wordfreq)
        
        best_sim = 0
        best_topic = ""
        for topic in self.topic_tfidf.keys():
            sim = self.__cosine_sim(topic)
            if sim >= best_sim:
                best_topic = topic
                best_sim = sim 
        
        return best_topic
        
    def __cosine_sim(self, topic):
        """
        Measure the cosine similarity value between the news and the topic.
        @param topic : the target AI topic
        @type topic : C{string}
        """
        tfidf1 = self.target_tfidf
        tfidf2 = self.topic_tfidf[topic]
        
        sim = 0
        for id in tfidf1.keys():
            if id in tfidf2.keys():
                sim += tfidf1[id]*tfidf2[id]
            
        return sim
       
    def __normalize_wordfreq(self, wordfreq):
        """
        Normalize the wordfreq by the freqency (ease the diff between long
        story and short story).
        @param wordfreq: the word freqency of the bag of words of the news.
        @type wordfreq: C{nltk.FreqDist}
        """
        tfidf = {}
        dist = 0
        for word in wordfreq.keys():
            if word in self.idf.keys():
                weight =  math.log(1.0 + wordfreq[word], 2) * self.idf[word]
                tfidf[word] = weight
                dist += weight * weight
        dist = math.sqrt(dist)
        for word in tfidf.keys():
            tfidf[word] /= dist
        
        return tfidf
