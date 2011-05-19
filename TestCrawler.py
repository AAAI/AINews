from AINewsCrawler import AINewsCrawler
######################################################################
#
#                       Running Script
#
######################################################################
def assign_topic(end):
    crawler = AINewsCrawler()
    
    for id in range(1, end):
        info = crawler.get_urlinfo(id)
        if info != None:
            category = crawler.find_topic(id)
            try:
                query = """ update urllist set category = '%s' where rowid = %d""" \
                    % (category, id)
                crawler.db.execute(query)
            except Exception as e:
                print "\tassign category error:", e
            print id, ":", category, ":\t",info[-2]
            
def crawl_url():
    crawler = AINewsCrawler()
    url = "http://www.clarin.com/internet/computadoras-hablan-mantienen-dialogos-humano_0_290371186.html"
    crawler.crawl_url(url)
            
def main():
    crawler = AINewsCrawler()
    crawler.crawl()
     
def test_find_topic():
    begindate = date.today() - timedelta(days = 14)
    crawler = AINewsCrawler(begindate)
    
    for id in range(100, 130):
        info = crawler.get_urlinfo(id)
        if info != None:    
            print id, ":", crawler.find_topic(id), ":\t",info[-2]
if __name__ == "__main__":
    main()
    #assign_topic(end=129)
    #crawl_url()

