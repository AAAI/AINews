"""
This is a human made duplicated news testing set used for experiment.
I manually making duplicated news pair from news id 314-664

This file records several experiment I made on the human collected
near-duplicated news to determine the best parameters.

It is not used in the main AINews procedures.

Author: Liang Dong
Date: Dec. 13th, 2010
"""
import time
from datetime import datetime

from AINewsDupManager import AINewsDupManager
from AINewsSim import AINewsSim
from LuceneSim import LuceneSim

"""
The following 20 pairs of duplicated news set
are manually created among 351 crawled AI news whose id are in range (314-664)
"""

duplists = [
    ([663, 664], "WikiLeak"),
    ([659, 661], "Robot Restaurant China"),
    ([629, 626, 625, 622, 620, 617, 618], "NewZealand Mine Crash"),
    ([601, 583, 633, 604], "Kinect hack"),
    ([582, 585], "Undersea Robot"),
    ([575, 580], "Mouse Robot"),
    ([465, 560, 566, 578], "Robot grip"),
    ([555, 552], "bionic arm driver die"),
    ([551, 553], "Weston-super-Mare pier reopen"),
    ([531, 543], "robot bowl"),
    ([539, 542], "battery smaller than salt"),
    ([529, 437], "robot yacht"),
    ([509, 512, 516], "robot census"),
    ([500, 501, 502, 505, 506, 508], "Google Robot car"),
    ([488, 503], "India movie"),
    ([483, 494], "Game Enslaved"),
    ([486, 479], "Underwater robot"),
    ([466, 476], "robot archer"),
    ([461, 471], "sensor spider web"),
    ([434, 435, 439], "nano wire skin"),
    ([419, 427], "robot snake"),
    ([400, 451], "robot swarm"),
    ([398, 407], "flying robot hand"),
    ([395, 397, 390], "robot soak oil"),
    ([384, 394], "robot nose smell"),
    ([367, 368], "Mar science"),
    ([348, 342], "robot wheelchair"),
    ([336, 329], "Robot Pyramid secret"),
    ([335, 349], "NASA Robonaut 2"),
    ([331, 334, 341, 369], "Spacewalker repair station"),
    ([323, 504], "Teleconference robot")
]

# ID range [314, 664]
id_begin = 314
id_end = 665
####################################
# idset records all the news id
####################################
idset = set()     # idset records all human selected news id
checklist = set() # checklist records all human selected dup pairs
for dupset in duplists:
    for id in dupset[0]:
        idset.add(id)
    n = len(dupset[0])
    sortedlist = sorted(dupset[0])
    for i in range(n-1):
        for j in range(i+1, n):
            checklist.add(tuple([sortedlist[i],sortedlist[j]]))

def create():
    dupmgr = AINewsDupManager()
    for dupset in duplists:
        dupmgr.create_dupset(dupset[0], dupset[0][0], dupset[1])
        
def compute_sim(aisim):
    group = 0
    for dupset in duplists:
        n = len(dupset[0])
        for i in range(n-1):
            for j in range(i+1, n):
                print group, dupset[0][i], dupset[0][j],
                print aisim.sim(dupset[0][i], dupset[0][j])
        group +=1


def frange(begin, end, step):
    while begin < end:
        yield begin
        begin += step
        
    
    
def recallprecision(urllist, aisim):
    """
    recall and precision for simularity method, make all pairs from urllist
    and compute the similarity.
    """
    truepos = {}
    falsepos = {}
    #cutoff range [0.05, 0.7]
    cutoff_begin = 10
    cutoff_end = 51
    for cutoff in range(cutoff_begin, cutoff_end):
        truepos[cutoff]=0
        falsepos[cutoff]=0
    
    total = 0
    pos = 0
    N = len(urllist)
    progress_step = N*(N-1)/200
    
    simvals = {}
    for i in range(0, N-1):
        print "Progress:", 1.0*total/progress_step, "%"
        for j in range(i+1, N):
            val = aisim.sim(urllist[i], urllist[j])
            total += 1
            simvals[(urllist[i], urllist[j])] = val
            if (urllist[i], urllist[j]) in checklist:
                flag = True
                pos += 1
            else:
                flag = False
                
            cutoff = cutoff_begin*0.01
            for x in range(cutoff_begin,cutoff_end):
                if val >= cutoff:
                    if flag:
                        truepos[x] += 1
                    else:
                        falsepos[x] += 1
                cutoff += 0.01
            
    best_cutoff = 0
    best_f1 = 0
    best_p = 0
    best_r = 0
    for cutoff in range(cutoff_begin, cutoff_end):
        if truepos[cutoff]==0 and falsepos[cutoff]==0:
            precision = 0
        else:
            precision = truepos[cutoff]*1.0/(truepos[cutoff]+falsepos[cutoff])
        recall = truepos[cutoff]*1.0/pos
        if precision == 0 and recall == 0:
            f1 = 0
        else:
            f1 = 2.0*(precision*recall)/(precision+recall)
        if f1 > best_f1:
            best_f1 = f1
            best_cutoff = cutoff
            best_p = precision
            best_r = recall
   
    print "cutoff:",best_cutoff*.01, "True Pos:", \
            truepos[best_cutoff], "False Pos:", falsepos[best_cutoff],\
            "precision:", best_p, "recall:", best_r, "f1:",best_f1
            
    for near in range(2, 6):
        for far in range(120,151,10):
            print near, far,
            aisim.set_temporal(near, far)
            pos = 0
            for cutoff in range(cutoff_begin, cutoff_end):
                truepos[cutoff]=0
                falsepos[cutoff]=0
            for i in range(0,N-1):
                for j in range(i+1, N):
                    val = simvals[(urllist[i], urllist[j])]
                    val *= aisim.temporal_coefficient(urllist[i],urllist[j])
                    if (urllist[i], urllist[j]) in checklist:
                        flag = True
                        pos += 1
                    else:
                        flag = False
                        
                    cutoff = cutoff_begin*0.01
                    for x in range(cutoff_begin,cutoff_end):
                        if val >= cutoff:
                            if flag:
                                truepos[x] += 1
                            else:
                                falsepos[x] += 1
                        cutoff += 0.01
            
            best_cutoff = 0
            best_f1 = 0
            best_p = 0
            best_r = 0
            for cutoff in range(cutoff_begin, cutoff_end):
                if truepos[cutoff]==0 and falsepos[cutoff]==0:
                    precision = 0
                else:
                    precision = truepos[cutoff]*1.0/(truepos[cutoff]+falsepos[cutoff])
                recall = truepos[cutoff]*1.0/pos
                if precision == 0 and recall == 0:
                    f1 = 0
                else:
                    f1 = 2.0*(precision*recall)/(precision+recall)
                if f1 > best_f1:
                    best_f1 = f1
                    best_cutoff = cutoff
                    best_p = precision
                    best_r = recall
                """
                print "cutoff:", cutoff*.01
                print "\tTrue Pos:", truepos[cutoff]
                print "\tFalse Pos:", falsepos[cutoff]
                print "\tpresision:",precision
                print "\trecall:", recall
                print "\tf1:", f1
                """
            print "cutoff:",best_cutoff*.01, "True Pos:", \
                    truepos[best_cutoff], "False Pos:", falsepos[best_cutoff],\
                    "precision:", best_p, "recall:", best_r, "f1:",best_f1
        
   
##########################################
#
#      Testing
#
##########################################

(CREATE, COSINE, COSINE_ONE, COSINE_RECALLPRECISION, LUCENE, LUCENE_ONE, LUCENE_RECALLPRECISION) = range(7)
SEPARATE,ALL,NOTITLE = range(3)

if __name__ == "__main__":
    start = datetime.now()
    type = COSINE_RECALLPRECISION
    
    
    # LuceneSim Parameters
    index_dir = "lucene/wiki"
    hit_num = 100
    querier_type = SEPARATE
    
    #range(314, 665), 48.0
    if type == CREATE:
        create()
    if type == COSINE:
        aisim = AINewsSim()
        compute_sim(aisim)
    elif type == COSINE_ONE:
        aisim = AINewsSim()
        print aisim.sim(314, 321)
    elif type == COSINE_RECALLPRECISION:
        aisim = AINewsSim()
        recallprecision(range(314, 665), aisim)
    elif type == LUCENE:
        aisim = LuceneSim(index_dir, hit_num, querier_type)
        compute_sim(aisim)
    elif type == LUCENE_ONE:
        aisim = LuceneSim(index_dir, hit_num, querier_type)
        print aisim.sim(314,321)
    elif type == LUCENE_RECALLPRECISION:
        aisim = LuceneSim(index_dir, hit_num, querier_type)
        recallprecision(range(314, 665), aisim)
    end = datetime.now()
    print end - start
   