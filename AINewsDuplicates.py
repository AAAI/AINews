from datetime import date, timedelta
from AINewsCorpus import AINewsCorpus
from AINewsConfig import config

def add_to_duplicates(duplicates, urlid1, urlid2):
    found = False
    for dupset in duplicates:
        if urlid1 in dupset or urlid2 in dupset:
            dupset.add(urlid1)
            dupset.add(urlid2)
            found = True
            break
    if not found:
        dupset = set()
        dupset.add(urlid1)
        dupset.add(urlid2)
        duplicates.append(dupset)

def compare_articles(article1, article2, sources):
    relevance1 = sources[article1['publisher']]
    relevance2 = sources[article2['publisher']]
    cat_count1 = len(article1['categories'])
    cat_count2 = len(article2['categories'])
    if cmp(relevance1, relevance2) == 0:
        return cmp(cat_count1, cat_count2)
    else:
        return cmp(relevance1, relevance2)

class AINewsDuplicates:
    def __init__(self):
        self.corpus = AINewsCorpus()

    def filter_duplicates(self, articles, sources):
        date_start = date.today() - timedelta(days = int(config['duplicates.days_back']))
        date_end = date.today()
        cutoff = float(config['duplicates.threshold'])
        all_articles = self.corpus.get_articles_daterange(date_start, date_end)
        duplicates = []
        similarities = {}

        urlids = sorted(all_articles.keys())
        for i in range(0, len(urlids) - 1):
            for j in range(i+1, len(urlids)):
                # only compare to articles that might be published this week
                if urlids[j] not in articles: continue

                tfidf1 = all_articles[urlids[i]]['tfidf']
                tfidf2 = all_articles[urlids[j]]['tfidf']
                similarity = self.corpus.cos_sim(tfidf1, tfidf2)

                if similarity >= cutoff:
                    # if article i has not been published
                    if not all_articles[urlids[i]]['published']:
                        add_to_duplicates(duplicates, urlids[i], urlids[j])
                        similarities[(urlids[i], urlids[j])] = similarity
                        similarities[(urlids[j], urlids[i])] = similarity
                    # if article i has already been published,
                    # then just don't publish article j
                    else:
                        articles[urlids[j]]['duplicates'] = \
                                [(urlids[i], all_articles[urlids[i]]['title'], similarity)]
                        if articles[urlids[j]]['publish']:
                            articles[urlids[j]]['publish'] = False
                            articles[urlids[j]]['transcript'].append(
                                    ("Rejected because duplicate (sim=%.3f, " +
                                    "cutoff=%.3f) of already published article %s") % \
                                            (similarity, cutoff, str(urlids[i])))

        for dupset in duplicates:
            for urlid in dupset:
                if urlid in articles:
                    dupset2 = dupset.copy()
                    dupset2.remove(urlid)
                    articles[urlid]['duplicates'] = \
                            map(lambda u: (u, articles[u]['title'], similarities[(u,urlid)]),
                                filter(lambda u: u in articles and (u,urlid) in similarities, dupset2))

            sorted_dups = sorted(filter(lambda u: u in articles and articles[u]['publish'], dupset),
                    cmp=lambda x,y: compare_articles(articles[x], articles[y], sources),
                    reverse = True)
            if(len(sorted_dups) > 1):
                # first in sorted set is chosen; rest are dumped
                articles[sorted_dups[0]]['transcript'].append("Preferred over duplicates")

                for urlid in sorted_dups[1:]:
                    if articles[urlid]['publish']:
                        articles[urlid]['publish'] = False
                        articles[urlid]['transcript'].append(("Rejected because duplicate " +
                                "%s was chosen instead") % sorted_dups[0])

