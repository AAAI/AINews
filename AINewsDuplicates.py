from datetime import date, timedelta
from AINewsCorpus import AINewsCorpus
from AINewsConfig import config

class AINewsDuplicates:
    def __init__(self):
        self.corpus = AINewsCorpus()

    def filter_duplicates(self, articles, sources):
        date_start = date.today() - timedelta(days = int(config['duplicates.days_back']))
        date_end = date.today()
        cutoff = float(config['duplicates.threshold'])
        all_articles = self.corpus.get_articles_daterange(date_start, date_end)

        urlids = sorted(all_articles.keys())
        for i in range(0, len(urlids) - 1):
            for j in range(i+1, len(urlids)):
                # only compare with articles that haven't been filtered out
                if urlids[j] not in articles \
                        or not articles[urlids[j]]['publish']:
                    continue

                tfidf1 = all_articles[urlids[i]]['tfidf']
                tfidf2 = all_articles[urlids[j]]['tfidf']
                similarity = self.corpus.cos_sim(tfidf1, tfidf2)

                if similarity >= cutoff:
                    print urlids[i],urlids[j],similarity

                    # if article i has already been published (processed),
                    # then just don't publish article j
                    if all_articles[urlids[i]]['processed']:
                        articles[urlids[j]]['publish'] = False
                        articles[urlids[j]]['transcript'].append(
                                'Rejected because duplicate (sim=%.3f, cutoff=%.3f) of already published article %s' % \
                                        (similarity, cutoff, str(urlids[i])))
                    # otherwise, neither article is published yet, so we have
                    # to decide which is definitive; the rule is take the
                    # article that comes from a more 'relevant' source, or, if
                    # sources are equally relevant, take the article with more
                    # categories
                    else:
                        if not articles[urlids[i]]['publish']: continue

                        # more relevant source is better
                        relevance1 = sources[articles[urlids[i]]['publisher']]
                        relevance2 = sources[articles[urlids[j]]['publisher']]
                        
                        if relevance1 > relevance2:
                            articles[urlids[j]]['publish'] = False
                            articles[urlids[j]]['transcript'].append(
                                    'Rejected because duplicate (sim=%.3f, cutoff=%.3f) of article %s, which comes from a more relevant source (%s:%d > %s:%d)' % \
                                            (similarity, cutoff, str(urlids[j]),
                                                articles[urlids[i]]['publisher'],
                                                relevance1,
                                                articles[urlids[j]]['publisher'],
                                                relevance2))
                        elif relevance2 > relevance1:
                            articles[urlids[i]]['publish'] = False
                            articles[urlids[i]]['transcript'].append(
                                    'Rejected because duplicate (sim=%.3f, cutoff=%.3f) of article %s, which comes from a more relevant source (%s:%d > %s:%d)' % \
                                            (similarity, cutoff, str(urlids[j]),
                                                articles[urlids[j]]['publisher'],
                                                relevance2,
                                                articles[urlids[i]]['publisher'],
                                                relevance1))

                        # if source relevance is the same, more categories is better
                        numcats_i = len(articles[urlids[i]]['categories'])
                        numcats_j = len(articles[urlids[j]]['categories'])
                        if numcats_i > numcats_j:
                            articles[urlids[j]]['publish'] = False
                            articles[urlids[j]]['transcript'].append(
                                    'Rejected because duplicate (sim=%.3f, cutoff=%.3f) of article %s, which has more categories' % \
                                            (similarity, cutoff, str(urlids[i])))
                        else:
                            articles[urlids[i]]['publish'] = False
                            articles[urlids[i]]['transcript'].append(
                                    'Rejected because duplicate (sim=%.3f, cutoff=%.3f) of article %s, which has more or equal number of categories' % \
                                            (similarity, cutoff, str(urlids[j])))
