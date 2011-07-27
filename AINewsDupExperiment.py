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

from AINewsCorpus import AINewsCorpus
from AINewsSim import AINewsSim
from AINewsDB import AINewsDB
from AINewsConfig import paths
from AINewsTools import loadpickle, savepickle
#from LuceneSim import LuceneSim

"""
The following 20 pairs of duplicated news set
are manually created among 351 crawled AI news whose id are in range (314-664)
"""

duplists = [
    ([1604, 1606], "Lovotics"),
    ([1073, 1072, 1067, 1066], "Geminoid"),
    ([1033, 1029], "paintball robot"),
    ([1019, 999], "Robots become self-aware"),
    ([996, 1002], "humanoid robot in space"),
    ([985, 987, 1004, 997, 1008, 1017, 1027], "Japan robot marathon"),
    ([995, 994, 996, 998, 1015, 1014, 1006, 1024, 986], "Shuttle Discovery"),
    ([929, 915], "Androidify"),
    ([914, 952], "X-prize"),
    ([896, 886, 935], "Robot internet"),
    ([901, 897], "Scones"),
    ([904, 902], "Baby robot"),
    ([884, 883], "Super bowl robot"),
    ([933, 946], "when robots attack"),
    ([861, 856], "Kno tablet"),
    ([846, 854], "Can machines fall in love"),
    ([833, 832], "Health checkup"),
    ([821, 831, 840], "robot babies"),
    ([834, 843], "quadrotors"),
    ([842, 850], "fingers"),
    ([857, 872], "rubber"),
    ([859, 879], "sick kids"),
    ([866, 871], "keepon"),
    ([869, 894], "ephaptic coupling"),
    ([824, 839, 847], "monkey see"),
    ([804, 811, 830, 878], "kinect"),
    ([716, 715, 717], "Korean teachers"),
    ([674, 676, 729], "CES 2011"),
    ([668, 667, 734, 794, 789, 787, 885, 881, 880, 893, 909, 925, 922, 921, 920, 918, 917, 934, 930, 926, 944, 942, 938, 937, 936, 955, 954, 958, 947, 963, 962, 968, 970, 973, 969, 1065, 1060], "Jeopardy Watson"),
    ([663, 664], "WikiLeak"),
    ([659, 661, 693, 688], "Robot Restaurant China"),
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
    ([323, 504], "Teleconference robot")]

duplist_stored = []
try:
    duplist_stored = loadpickle(paths['corpus.duplist'])
except:
    pass

notduplist_stored = set()
try:
    notduplist_stored = loadpickle(paths['corpus.notduplist'])
except:
    pass
duplists += duplist_stored

corpus = AINewsCorpus()

id_begin = 315
id_end = 1200
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
            checklist.add(tuple([int(sortedlist[i]),int(sortedlist[j])]))

def compute_sim(aisim):
    group = 0
    for dupset in duplists:
        n = len(dupset[0])
        for i in range(n-1):
            for j in range(i+1, n):
                print group, dupset[0][i], dupset[0][j],
                print aisim.sim(dupset[0][i], dupset[0][j])
        group +=1

def recallprecision(docs, aisim):
    """
    recall and precision for simularity method, make all pairs from urllist
    and compute the similarity.
    """
    truepos = {}
    falsepos = {}
    #cutoff range [0.01, 1.0]
    cutoff_begin = 0
    cutoff_end = 100
    for cutoff in range(cutoff_begin, cutoff_end):
        truepos[cutoff]=0
        falsepos[cutoff]=0
    
    total = 0
    pos = 0
    N = len(docs)
    progress_step = N*(N-1)/200.0
    
    simvals = {}
    for i in range(0, N-1):
        if (i % (N/10)) == 0:
            print "Progress: %.0f%%" % (float(total)/progress_step)
        for j in range(i+1, N):
            key = (int(docs[i][0]), int(docs[j][0]))
            val = corpus.sim(docs[i], docs[j])
            total += 1
            simvals[key] = val
            if key in checklist:
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
                        #if cutoff >= 0.1 and cutoff < 0.11:
                        #    print "false pos:", key, cutoff
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
            precision = float(truepos[cutoff])/(truepos[cutoff]+falsepos[cutoff])
        if pos == 0:
            recall = 0
        else:
            recall = float(truepos[cutoff])/pos
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
    print

    """
    db = AINewsDB()
    done = False
    for i in range(0, N-1):
        if done: break;
        for j in range(i+1, N):
            if done: break;
            key = (int(docs[i][0]), int(docs[j][0]))
            if key in notduplist_stored: continue
            val = corpus.sim(docs[i], docs[j])
            if key not in checklist and val >= (best_cutoff*0.01):
                (title1, desc1, date1) = db.selectone( \
                        "select title,description,pubdate from urllist " +
                        "where rowid = %s" % docs[i][0])
                (title2, desc2, date2) = db.selectone( \
                        "select title,description,pubdate from urllist " +
                        "where rowid = %s" % docs[j][0])
                print "-- %s (%s)\n\n%s\n\n-- %s (%s)\n\n%s\n\n" % \
                        (title1, str(date1), desc1, title2, str(date2), desc2)
                answer = raw_input("Duplicates? (y/n/q): ")
                if answer == "y" or answer == "Y":
                    duplist_stored.append(([key[0], key[1]], "duplist_stored"))
                if answer == "n" or answer == "N":
                    notduplist_stored.add(key)
                elif answer == "q" or answer == "Q":
                    done = True
                print "\n\n----------------\n\n"
    savepickle(paths['corpus.notduplist'], notduplist_stored)
    savepickle(paths['corpus.duplist'], duplist_stored)

    """
            
    for near in range(1, 21, 2):
        for far in range(1, 21, 2):
            if near > far: continue
            print near, far,
            aisim.set_temporal(near, far)
            pos = 0
            for cutoff in range(cutoff_begin, cutoff_end):
                truepos[cutoff]=0
                falsepos[cutoff]=0
            for i in range(0,N-1):
                for j in range(i+1, N):
                    key = (int(docs[i][0]), int(docs[j][0]))
                    val = simvals[key]
                    val *= aisim.temporal_coefficient(docs[i][3], docs[j][3])
                    if key in checklist:
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

    urllist = map(lambda urlid: str(urlid), range(id_begin, id_end))

    (train_corpus, predict_corpus) = corpus.load_corpus( \
            "urllist:urllist:"+','.join(urllist), 1.0, True)
    
    # LuceneSim Parameters
    index_dir = "lucene/wiki"
    hit_num = 100
    querier_type = SEPARATE
    
    if type == COSINE_RECALLPRECISION:
        aisim = AINewsSim()
        recallprecision(train_corpus, aisim)
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
   
