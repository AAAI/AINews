"""
This is a human made duplicated news testing set used for experiment.
I manually making duplicated news pair from news id 314-664

Author: Liang Dong
Date: Dec. 13th, 2010
"""

from AINewsDupManager import AINewsDupManager

"""
The following 20 pairs of duplicated news set
are manually created among crawled AI news id range (314-664)
"""
duplists = [
    ([663, 664], "WikiLeak"),
    ([659, 661], "Robot Resturant China"),
    ([629, 626, 625, 622, 620, 617], "NewZealand Mine Crash"),
    ([601, 604], "Kinect hack"),
    ([582, 585], "Undersea Robot"),
    ([575, 580], "Mouse Robot"),
    ([555, 552], "bionic arm driver die"),
    ([531, 543], "robot bowl"),
    ([509, 512], "robot census"),
    ([500, 501, 502, 505, 506, 508], "Google Robot car"),
    ([483, 494], "enslaved game"),
    ([466, 476], "robot archer"),
    ([434, 435], "nano wire skin"),
    ([419, 427], "robot snake"),
    ([398, 407], "flying robot hand"),
    ([395, 390], "robot soak oid"),
    ([384, 394], "robot nose smell"),
    ([367, 368], "mar science"),
    ([348, 342], "robot wheelchair"),
    ([334, 331], "nasa spacewalk")
]

dupmgr = AINewsDupManager()
for dupset in duplists:
    dupmgr.create_dupset(dupset[0], dupset[0][0], dupset[1])
