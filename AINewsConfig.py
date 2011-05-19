"""
AINewsConfig reads the configure file: config.ini.
It parses the config.ini as well as pre-define several static parameters.
"""

import sys
from AINewsTools import loadconfig

# Load those user configable parameters
config =  loadconfig("config.ini")

lib_dir = config['ainews.lib_dir']
sys.path.append(lib_dir)


# The location of the AINewsFinder's directory for Python files.
ainews_root = config['ainews.ainews_root']

# The whitelist_unigrams, bigrams and trigrams are used to filter those
# un-related news articles in the first place. Any news should at least
# contain one of the those terms to be considered news candidates.
whitelist_unigrams = frozenset(config['crawler.whitelist_unigrams'].split(":"))
whitelist_bigrams  = frozenset(config['crawler.whitelist_bigrams'].split(":"))
whitelist_trigrams = frozenset(config['crawler.whitelist_trigrams'].split(":"))

# aitopic_urls is used to assign each news to a category by comparing the
# similarity with the following webpages.
aitopic_urls = [
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/AIOverview",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Agents",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Applications",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/CognitiveScience",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Education",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Ethics",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Games",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/History",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Interfaces",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/MachineLearning",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/NaturalLanguage",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Philosophy",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Reasoning",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Representation",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Robots",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/ScienceFiction",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Speech",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Systems",
    "http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Vision"
   ]

"""
Regular expression used to extract the date from text
key: dateformat
value: (regular expression, time str parsing)
"""
dateformat_regexps = {
    "Mon. DD, YYYY" : ("(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\. (0?[1-9]|[12][0-9]|3[01]), 20\d\d", "%b. %d, %Y"),
    "Mon DD, YYYY" : ("(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (0?[1-9]|[12][0-9]|3[01]), 20\d\d","%b %d, %Y"),
    "Month DD, YYYY" : ("(January|February|March|April|May|June|July|August|September|October|November|December) (0?[1-9]|[12][0-9]|3[01]), 20\d\d", "%B %d, %Y"),  
    "DD Month, YYYY" : ("(0?[1-9]|[12][0-9]|3[01]) (January|February|March|April|May|June|July|August|September|October|November|December), 20\d\d", "%d %B, %Y"),
    "DD Month YYYY" : ("(0?[1-9]|[12][0-9]|3[01]) (January|February|March|April|May|June|July|August|September|October|November|December) 20\d\d", "%d %B %Y"),
    "Mon DD YYYY" : ("(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (0?[1-9]|[12][0-9]|3[01]) 20\d\d", "%b %d %Y"),
    "Month DD YYYY" : ("(January|February|March|April|May|June|July|August|September|October|November|December) (0?[1-9]|[12][0-9]|3[01]) 20\d\d","%B %d %Y"),
    "YYYY-MM-DD" : ("20\d\d\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])", "%Y-%m-%d"),
    "MM/DD/YYYY" : ("(0[1-9]|1[012])\/(0[1-9]|[12][0-9]|3[01])\/(19|20)\d\d", "%m/%d/%Y"),
    "DD Mon YYYY" : ("(0?[1-9]|[12][0-9]|3[01]) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) 20\d\d", "%d %b %Y"),
    "DD/MM/YYYY" : ("(0?[1-9]|[12][0-9]|3[01])\/(0?[1-9]|1[012])\/20\d\d","%d/%m/%Y")
}

