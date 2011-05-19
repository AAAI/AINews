from AINewsParser import *

######################################################################
#
#                       Running Script
#
######################################################################
def test_extract_content():
    parser = AINewsParser(debug = True)
    #url = "http://www.bbc.co.uk/worldservice/haveyoursay/2010/06/100611_team_talk_review.shtml"
    #url = "http://www.zdnet.co.uk/news/infrastructure/2010/07/09/ec-adopts-26m-cross-border-services-programme-40089497/"
    url = "http://www.bbc.co.uk/worldservice/documentaries/2010/06/100608_doc_south_africa_soyinka.shtml"
    #url = "http://news.cnet.com/8301-17938_105-20007837-1.html"
   # url = "http://www.computerweekly.com/Articles/2010/07/09/241908/EU-to-resume-sending-banking-details-to-US-in-August.htm"
   # url = "http://www.nytimes.com/2010/01/21/technology/personaltech/21headphones.html?_r=1&scp=10&sq=%22artificial%20intelligence%22&st=nyt"
    url = "http://sify.com/news/artificial-intelligence-system-to-improve-team-sports-news-scitech-khnpuicbeah.html"
    res = parser.parse_url(url)
    if res == False: return
    parser.extract_content(extractdate = True)
    parser.print_content()
    
def parse_sigleurl():
    parser = AINewsParser(debug = True)
    
    url = "http://www.nytimes.com/2010/07/06/nyregion/06heat.html?hp"
    
    res = parser.parse_url(url)
    if res == False: return 
    
    parser.extract_content()
    parser.print_content()
    parser.clear()    
  
if __name__ == "__main__":
    #parse_sigleurl()
    test_extract_content()
