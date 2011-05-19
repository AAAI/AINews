#!/usr/bin/env python

from AINewsSummarizer import AINewsSummarizer
from AINewsTools import loadfile2, loadpickle

s = AINewsSummarizer()
input = """
One way that political prisoners maintained their humanity during the apartheid years in this notorious place was to form a soccer league, the Makana Football Association, which operated from 1969 until 1991 and which has received international attention in retrospect during the World Cup.

Soccer brought relief from the exhausting life of breaking rocks in a quarry. It conferred dignity on prisoners subjected to beatings and humiliating body-cavity searches and meals of thin porridge streaked with tracings of worms and bird droppings. It provided a means of resistance, organization and unity to leaders of rival political parties, the African National Congress and the Pan-Africanist Congress, who found in a game a means of bonding and harnessing their opposition to the apartheid system. 

"""

sum = s.summarize(input, 1)
print "TEXT:", input
print "SUMM:", sum
