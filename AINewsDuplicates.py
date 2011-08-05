from datetime import date, timedelta
from AINewsCorpus import AINewsCorpus
from AINewsConfig import config

class AINewsDuplicates:
    def __init__(self):
        self.corpus = AINewsCorpus()
        self.sources = config['ranker.source_order'].split(':')

    def filter_duplicates(self, articles):
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
                    # article that comes from a more 'reputable' source
                    else:
                        if not articles[urlids[i]]['publish']: continue

                        # more categories is better
                        numcats_i = len(articles[urlids[i]]['categories'])
                        numcats_j = len(articles[urlids[j]]['categories'])
                        #print numcats_i, numcats_j
                        if numcats_i > numcats_j:
                            articles[urlids[j]]['publish'] = False
                            articles[urlids[j]]['transcript'].append(
                                    'Rejected because duplicate (sim=%.3f, cutoff=%.3f) of article %s, which has more categories' % \
                                            (similarity, cutoff, str(urlids[i])))
                        elif numcats_j > numcats_i:
                            articles[urlids[i]]['publish'] = False
                            articles[urlids[i]]['transcript'].append(
                                    'Rejected because duplicate (sim=%.3f, cutoff=%.3f) of article %s, which has more categories' % \
                                            (similarity, cutoff, str(urlids[j])))

                        # otherwise, earlier position in sources is better
                        source1 = self.sources.index(articles[urlids[i]]['publisher'])
                        source2 = self.sources.index(articles[urlids[j]]['publisher'])
                        
                        if source1 < source2:
                            articles[urlids[j]]['publish'] = False
                            articles[urlids[j]]['transcript'].append(
                                    'Rejected because duplicate (sim=%.3f, cutoff=%.3f) of article %s, which comes from a better source (%s)' % \
                                            (similarity, cutoff, str(urlids[j]), self.sources[source1]))
                        else:
                            articles[urlids[i]]['publish'] = False
                            articles[urlids[i]]['transcript'].append(
                                    'Rejected because duplicate (sim=%.3f, cutoff=%.3f) of article %s, which comes from a better or the same source (%s)' % \
                                            (similarity, cutoff, str(urlids[i]), self.sources[source2]))
