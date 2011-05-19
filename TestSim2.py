from AINewsSim import AINewsSim
from AINewsTools import unescape
from AINewsConfig import config
from operator import  itemgetter


s = AINewsSim()


for i in range(500, 503):
    for j in range(i+1, 503):
        val = s.sim(i,j)
        print i, j, val
      


