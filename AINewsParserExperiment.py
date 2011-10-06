
from AINewsCorpus import AINewsCorpus
from AINewsConfig import paths
from AINewsTools import trunc
import sys
sys.path.append(paths['libraries.tools'])
import justext
import os
import glob
import re
import ents
from subprocess import *


### modified from: http://www.korokithakis.net/posts/finding-the-levenshtein-distance-in-python/
def levenshtein_distance(first, second):
    """Find the Levenshtein distance between two arrays of strings."""
    if len(first) > len(second):
        first, second = second, first
    if len(second) == 0:
        return len(first)
    first_length = len(first) + 1
    second_length = len(second) + 1
    distance_matrix = [[0] * second_length for x in range(first_length)]
    for i in range(first_length):
       distance_matrix[i][0] = i
    for j in range(second_length):
       distance_matrix[0][j]=j
    for i in xrange(1, first_length):
        for j in range(1, second_length):
            deletion = distance_matrix[i-1][j] + 1
            insertion = distance_matrix[i][j-1] + 1
            substitution = distance_matrix[i-1][j-1]
            if first[i-1] != second[j-1]:
                substitution += 1
            distance_matrix[i][j] = min(insertion, deletion, substitution)
    return distance_matrix[first_length-1][second_length-1]


def evaluate():
    corpus = AINewsCorpus()
    print "urlid,length truewords,length justext,length goose,ld justtext,ld goose"
    for filename in sorted(glob.glob("../../experiments/justext/*.true")):
        truetext = ents.convert(file(filename).read())
        truetext = re.sub(r'[^\w\s]', ' ', trunc(truetext, max_pos=3000, ellipsis=False))
        truewords = re.split(r'\s+', truetext)
        urlid = filename[26:30]
        article = corpus.get_article(urlid)
        if article == None: continue
        articletext = re.sub(r'[^\w\s]', ' ', trunc((article['content_all']).encode('ascii'), max_pos=3000, ellipsis=False))
        articlewords = re.split(r'\s+', articletext)
        goosecmd = "cd /home/josh/aitopics/AINews/tools/goose; /opt/maven/bin/mvn exec:java -Dexec.mainClass=com.jimplush.goose.TalkToMeGoose -Dexec.args='%s' -q 2>>/home/josh/log.txt" % article['url']
        (stdout, _) = Popen(goosecmd, shell = True, stdout = PIPE).communicate()
        goosetext = ents.convert(stdout.encode('ascii'))
        goosetext = re.sub(r'[^\w\s]', ' ', trunc(goosetext, max_pos=3000, ellipsis=False))
        goosewords = re.split(r'\s+', goosetext)
        ld_1 = (levenshtein_distance(truewords, articlewords))/float(len(truewords))
        ld_2 = (levenshtein_distance(truewords, goosewords))/float(len(truewords))
        print "%s,%d,%d,%d,%.4f,%.4f" % \
            (urlid, len(truewords), len(articlewords), len(goosewords), ld_1, ld_2)


evaluate()
