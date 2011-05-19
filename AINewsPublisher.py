"""
AINewsPublisher generates the ranked latest news into different output format.
It publish to the PmWiki website and send email to subscriber. Facebook page
can be added in the future task.

The pmwiki page utilizes the AINewsPmwiki.php file to transfer the output file
into PmWiki format.
"""
import feedparser
import PyRSS2Gen
from os import path, mkdir
from glob import glob
from subprocess import *
from datetime import date, datetime, timedelta
from operator import itemgetter
from AINewsTools import loadpickle, savefile,savepickle
from AINewsConfig import config, aitopic_urls

class AINewsPublisher():
    def __init__(self):
        self.debug = config['ainews.debug']
        self.today = date.today()
        self.topicids = {"AIOverview":0, "Agents":1, "Applications":2,
           "CognitiveScience":3, "Education":4,"Ethics":5, 
           "Games":6, "History":7, "Interfaces":8, "MachineLearning":9,
           "NaturalLanguage":10, "Philosophy":11, "Reasoning":12,
           "Representation":13, "Robots":14, "ScienceFiction":15,"Speech":16,
           "Systems":17,  "Vision":18}

        topnews_unfiltered = loadpickle("output/topnews.pkl")
        ## filter topnews, so as to select only a few stories from each topic
        stories_per_topic = int(config['publisher.stories_per_topic'])
        self.topnews = []
        for topic in self.topicids.keys():
            news = filter(lambda n: n['topic'] == topic, topnews_unfiltered)
            self.topnews += news[:stories_per_topic]
        self.topnews = sorted(self.topnews, key=itemgetter('score'), reverse=True)
        
        currmonth = self.today.strftime("%Y-%m")
        p = "output/monthly/" + currmonth
        if not path.exists(p):
            mkdir(p)
        savepickle(p+"/"+self.today.strftime("%d"), self.topnews)
        
        self.semiauto_email_output = ""
        
    def generate_standard_output(self): 
        """
        Generate the stanard output for debuging on screen.
        """
        std_output = ""
        for news in self.topnews:
            std_output += """%f\t(%d) %s - (%s)\n%s\t%s\n\n""" \
                      % (news['score'], news['urlid'], news['title'], \
                         news['pubdate'], news['topic'], news['url'])
        savefile("output/std_output.txt", std_output.encode('utf-8'))
        
        
    
    def generate_email_output(self):
        """
        Generate the output for email format.
        """
        email_output = """
        <style type="text/css">
        a {
            color: #004466;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        p {
            font-family: Tahoma, Verdana, Arial, Helvetica, sans-serif;	
            font-size: 11px; 
            line-height: 18px;
            clear:both;
        }
        </style>
        
        <TABLE id=master cellSpacing=0 cellPadding=0 width=639 border=0 align="left" style="font-family: Tahoma, Verdana, Arial, Helvetica, sans-serif;	font-size: 11px; color: #5E5E5E; ">
        <TBODY>
            <TR >
                <TD >
                    <a name='top' id='top'></a>
                    <!-- Banner -->
                    <img style="" width='639px' height='45px' alt="AAAI - AI Alert" title="AAAI - AI Alert" src='http://www.aaai.org/AITopics/pmwiki/pub/images/aialertbannerv2.jpg' />
                    
                    <div>&nbsp;</div>
                    
                    
                    <table width='100%' cellpading='10' style="font-family: Tahoma, Verdana, Arial, Helvetica, sans-serif;	font-size: 11px; line-height: 18px;" >
                        <tr>
                            <td valign='top'>
                                
                                    Compiled from the <a style="color: #004466;" href='http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/AINews'>AI in the News</a> collection of
                                    <a style="color: #004466;" href='http://www.aaai.org/AITopics/'>AI Topics</a>.
                                    An <a href='http://www.aaai.org/AITopics/xml/rss/news.xml' style="color:#ff5a00;"><span style="color:#ff5a00;"><b>RSS</b></span></a>
                                     feed is also available.
                                    <a style="border-width:0px;" href='http://www.aaai.org/AITopics/xml/rss/news.xml'>
                                        <img style="border-width:0px;" src="http://www.aaai.org/aitopics/pmwiki/pub/images/rss.gif"/>
                                    </a>
                                    <br/><br/>
                                <div style="margin:0px 0px 10px 0px; ">
                                <img width='14px' height='10px' src='http://www.aaai.org/AITopics/pmwiki/pub/skins/aaaiblue/backgrounds/bulletSpaced.gif'>
                                <span style='clear:right; font-family: Tahoma, Verdana, Arial, Helvetica, sans-serif; color: #202020;font-size: 13px; line-height: 18px;'>
                                <b>LATEST HEADLINES - """+self.today.strftime("%B %d, %Y")+""" </b>
                        </span>
                                            </div>
                                            <img src='http://www.aaai.org/AITopics/pmwiki/pub/skins/aaaiblue/backgrounds/backgrounds07.gif' width='377px' height='25px'>
                                            
                                            <ul style='margin-top: 10px;  font-family: Tahoma, Verdana, Arial, Helvetica, sans-serif; font-size: 11px; line-height: 18px; color: #5E5E5E;'>
                """ 

        for id, news in enumerate(self.topnews):
            email_output += """<li><a style='color: #004466;' href='#anchor""" + str(id) + \
                "'>" + news['title'] + """</a>   
                <span style="font-size:83%">"""+news['topic']+""" </span> 
                </li> """ 
        
        email_output +=  \
"""
                                </ul>
                                <br>
                            </td>
                        </tr>
                        <tr>
                            <td width="639px" valign="top" style=" font-size: 11px; line-height: 18px ">
                            <img width='639px' height='30px' src='http://www.aaai.org/AITopics/pmwiki/pub/skins/aaaiblue/backgrounds/backgrounds16.jpg'>
                            
                            <div>&nbsp;</div>
                            <div style="margin:5px 0px 10px 0px; ">
                                <img width='14px' height='10px' src='http://www.aaai.org/AITopics/pmwiki/pub/skins/aaaiblue/backgrounds/bulletSpaced.gif'>
                                <span style='clear:right; font-family: Tahoma, Verdana, Arial, Helvetica, sans-serif; color: #202020;font-size: 13px; line-height: 18px;'>
                                    <b>SUMMARIES</b>
                                </span>
                            </div>
                            <img src='http://www.aaai.org/AITopics/pmwiki/pub/skins/aaaiblue/backgrounds/backgrounds07.gif' width='377px' height='25px'>
                
                <ul style="font-family: Tahoma, Verdana, Arial, Helvetica, sans-serif;	font-size: 11px; line-height: 18px; color: #5E5E5E;">

<!--CONTENT/BLURBS-->
"""
                        
        for id, news in enumerate(self.topnews):
            try:
                email_output += """
<li style='margin-top:15px; margin-bottom: 15px;' >
    %s:&nbsp; <strong><a target='_blank' name = 'anchor%d' style='color: #004466;' href='%s' rel='nofollow'>%s</a></strong> 
    &nbsp;%s
    <div style='text-align:right; margin:1px 0px 0px 0px'>
        <img src='http://www.aaai.org/AITopics/pmwiki/pub/images/next_arrow1.gif' alt='' title='' /> 
        <a class='wikilink' style='color: #004466;' href='%s'>%s</a>  &nbsp;&nbsp;&nbsp;<a href='#top'>
            <img  border='0px' style='margin-bottom:-1px' src='http://www.aaai.org/AITopics/pmwiki/pub/images/up_arrow1.gif'
            alt='back to top' title='back to top' />
        </a>
    </div>
</li>""" % (news['pubdate'].strftime("%B %d, %Y"), id, news['url'], news['title'], \
        news['desc'], aitopic_urls[self.topicids[news['topic']]], news['topic'])
            except Exception, e:
                print "Email output error.", e
        
        email_output += """                
                <!--END CONTENT/BLURBS-->
        </ul>
                                </td>
                            </tr>
                        </table>
                        <br />
                        <!-- Footer -->
                        
                    </TD>
                </TR>
                <TR><TD><span style="color: #5E5E5E;">
        <div style="width=100%; clear:both"> </div>
        """
        savefile("output/email_output.txt", email_output.encode('utf-8'))
        self.semiauto_email_output = email_output
        
    def generate_pmwiki_output(self):
        """
        Genereate the output with PmWiki page format. It need to be further
        processed by AINewsPmwiki.php.
        """
        header = """
(:keywords AI, artificial intelligence, AAAI, Association for the Advancement of Artificial Intelligence, formerly American Association for Artificial Intelligence, AI Topics, pathfinder, computer science, cognitive science, robots, agents, games, puzzles, expert systems, natural language, LISP, history, philosophy, bibliography, news, newspaper, magazine, science fiction, smart rooms, vision, speech, machine learning, chess, education, intelligent tutoring, reasoning, inference, logic, representation, ontology, turing, space, medicine, law, applications, overview, interface :)
----
[[#top]]
(:head:)AI in the News: Interesting News Stories about AI(:headend:)
----
(:contentbox:)
<div id=Contents>Contents</div>
*[[#recent | Recent News Stories]]
*[[#feeds| RSS Feeds by Topic]]
*%newwin%[[http://www.aaai.org/cgi-dada/mail.cgi | Subscribe to News Alerts]]  
*[[AITopics/NewsArchive | News Archive]]
*[[#additional | Additional News Collections]]
*[[AITopics/AINewsProcedure| Details About NewsFinder]]
(:contentboxend:)

''AI in the News'' is a AAAI service to alert readers to current stories about AI that appear in various news sources.  An AI program, NewsFinder, crawls the web to collect stories that mention a few key terms, like "artificial intelligence" or "robot", parses them, scores them with respect to likely interest to readers, and publishes the highest scoring stories here.  NewsFinder uses a Support Vector Machine that has been trained to classify the interestingness of stories (and is retrained frequently from readers' feedback) to score every story, then adjusts the scores up or down using knowledge of words and phrases that indicate more or less interest.

We hope you will contribute your own ratings. If a story is not relevant to ''AI in the News'' readers, it warrants a zero. Otherwise, use the 1-5 scale to rate how relevant and interesting a story is to readers. Click on the Rate button to submit your rating.

Stories are selected and published to ''AI in the News'' by the [[AINewsProcedure |  '''NewsFinder''']] program.

<div style="clear:both;"></div>
[[#recent]]
(:sectiontitle:)Recent News Stories - """ + self.today.strftime("%B %d, %Y") + "(:sectiontitleend:)\n"

        
        pmwiki_output = header
        pmwiki_output_norater = header
        for i, news in enumerate(self.topnews):
            pmwiki_output += """*%%newwin%% %s: [[%s| %s]].  %s.  &quot;%s&quot;%%%%([[info->AIArticles.%s]]) 	%%rfloat%%[[#top | ImageDir:up_arrow1.gif"back to top"]]\n->ImageDir:next_arrow1.gif [[AITopics/%s | %s]]  (:rater %d:)[[<<]]\n""" % \
                   (news['pubdate'].strftime("%B %d, %Y"), news['url'], news['title'],  news['publisher'], news['desc'], self.today.strftime("%Y-")+str(news['urlid']), news['topic'], news['topic'], news['urlid'])
            pmwiki_output_norater +="""*%%newwin%% %s: [[%s| %s]].   %s.  &quot;%s&quot;%%%%([[info->AIArticles.%s]]) 	%%rfloat%%[[#top | ImageDir:up_arrow1.gif"back to top"]]\n->ImageDir:next_arrow1.gif [[AITopics/%s | %s]][[<<]]\n\n""" % \
                   (news['pubdate'].strftime("%B %d, %Y"), news['url'], news['title'], news['publisher'], news['desc'], self.today.strftime("%Y-")+str(news['urlid']), news['topic'], news['topic'])
            
        """
        for i, news in enumerate(self.topnews):
            pmwiki_output += "!!%d. [[%s|%s]] [[<<]]%s | by \'\'%s (%s)\'\'[[<<]]\n%s(:rater %d:)\n----\n" % \
                    (i+1, news['url'], news['title'], news['topic'], news['publisher'], news['pubdate'], news['desc'], news['urlid'])
            pmwiki_output_norater += "!!%d. [[%s|%s]][[<<]]%s |  by \'\'%s (%s)\'\' [[<<]]\n%s \n" % \
                    (i+1, news['url'], news['title'], news['topic'], news['publisher'], news['pubdate'], news['desc'])
            if self.debug:
                debug_out = "[[<<]]Testing:{score:%f, ID:%d}[[<<]]\n" % (news['score'], news['urlid'])
                pmwiki_output_norater += debug_out
            pmwiki_output_norater += "----\n"
        """
        
        footer = """[[#feeds]]
----
[[#feeds]]
(:rsstitle:)RSS FEEDS (:rsstitleend:)
[-[[SiteDir:xml/rss/news.xml | General]] | [[SiteDir:xml/rss/agent.xml | Agents]] | [[SiteDir:xml/rss/apps.xml | Applications]] | [[SiteDir:xml/rss/cogsci.xml | Cognitive Science]] | [[SiteDir:xml/rss/edu.xml | Education]] | [[SiteDir:xml/rss/ethsoc.xml | Ethical &amp; Social Implications]] |  [[SiteDir:xml/rss/expert.xml | Expert Systems]] | [[SiteDir:xml/rss/game.xml | Games &amp; Puzzles]] | [[SiteDir:xml/rss/hist.xml | History]] | [[SiteDir:xml/rss/interf.xml | Interfaces]] | [[SiteDir:xml/rss/ml.xml | Machine Learning]] | [[SiteDir:xml/rss/nlp.xml | Natural Language Processing]] | [[SiteDir:xml/rss/phil.xml | Philosophy]] | [[SiteDir:xml/rss/reason.xml | Reasoning]] | [[SiteDir:xml/rss/rep.xml | Representation]] | [[SiteDir:xml/rss/robot.xml | Robots]] | [[SiteDir:xml/rss/robovid.xml | Robot Videos]] | [[SiteDir:xml/rss/scifi.xml | Science Fiction]] | [[SiteDir:xml/rss/speech.xml | Speech]] | [[SiteDir:xml/rss/systems.xml | Systems &amp; Languages]] | [[SiteDir:xml/rss/turing.xml | Turing Test]] | [[SiteDir:xml/rss/vision.xml | Vision]]-]


[[#additional]]
----
(:headlinestitle:)Additional News Collections(:headlinestitleend:)

(:if false:)
----
[[#pages]]
(:sectiontitle:)Related Pages(:sectiontitleend:)
(:ifend:)
(:table width=100%:)
(:cellnr:)
'''AI Topics Pages'''
* [[AITopics/NewsArchive | ''AI in the News'' Archive]] - Previously featured articles 
* '''AI Alert''' - the biweekly ''AI in the News'' email update [[#aialert]]
** %newwin%[[http://www.aaai.org/cgi-dada/mail.cgi | '''Subscribe/unsubscribe''']]
** Prior to July, 2008, AI Alert pages were separate from ''AI in the News'' pages. To see the older AI Alert pages, visit the [[AITopics/AIAlert | AI Alert Archive]].
* [[AITopics/NewsSources | AI News Sources &amp; Collections]] including AI-Generated News
* [[AITopics/AINewsToons | AI News Toons]]
* [[AITopics/AINewsColumn | Quarterly ''AI in the News'' column]] in AI Magazine
* [[AITopics/JournalistResources | Resources for Journalists]] 
* [[AITopics/AIEffect | &quot;The AI Effect&quot;]] 
* [[AITopics/History#thisday | This Day in History]]

'''Other AI Topics Multimedia Collections'''
*[[AIVideos/HomePage | AI Videos]]
*[[AITopics/ShowTime | It's Show Time]]

'''AI News Pages Maintained by Others'''
*[[http://aboutai.com/news/ | AboutAI]] - Latest News Articles on AISolver.com
*%newwin%[[http://www.robotreviews.com/news | Robot News]] - from robot reviews
*%newwin%[[http://www.roboticsbusinessreview.com/ | Robotics Business Review > Commercial Uses of Robotics]], a subscription-based service, with some articles and abstracts, and all headlines, available for free.
*%newwin%[[http://ehpub.bm23.com/public/?q=preview_message&fn=Link&t=1&ssid=5300&id=dqf0e9l4ff9bhexxcijh45hhp6vmv&id2=fij3n0yzmzrh44b6n5dapkviu3jtv&subscriber_id=atbtkqjmtxpzjrdyzdtehggsfoutbgc&messageversion_id=azgmlnzlrjehdkxdguxhoebxggfrbpj&delivery_id=bhhdtnmwhjeevgccoebngfnjeqixbgm&tid=1.438.C7wD6w~B4a6.1hnz5..C7wD7g~J9Qk.B9AD6~BXPzv.l.B9AD7~cUb.x6YX9Q | Robotics Trends]]  - subscribe to the online newsletter for news about robots
*%newwin%[[http://www.sciencedaily.com/news/computers_math/artificial_intelligence/ | Science Daily]] News about AI
*%newwin%[[http://www.scientificamerican.com/search/index.cfm?i=1&q=robots&sort=publish_date&submit=submit&submit.x=0&submit.y=0&u1=q | Scientific American]] Stories about Robots

(:cell align=center valign=top:) ArtDir:clipperboat.jpg"AI news clipper logo"
(:tableend:)


----
'-[[#art]]'''PLEASE NOTE:''' 1) because %red%an excerpt may not reflect the overall tenor of the article%% from which it was harvested, %red%nor contain all of the relevant information%%, you are '''''strongly encouraged''''' to %red%read the entire article%%; 2) please remember that the news is offered &quot;[[AITopics/Notices | '''{+as is+}''']]&quot; and the fact that an article has been selected does not imply any endorsement whatsoever; 3) Please be aware that the content of an external third party site may have changed since we established our link to it. ''If you decide to access these Websites, you do so at your own risk; ''4) please respect the rights of the [[AITopics/Notices#copy | copyright]] holders; and as explained in detail in our [[AITopics/Notices | Notices &amp; Disclaimers]],'' %red%just because we mention something on this page, you should not infer that...%%''-'

>>comment<<
(:if enabled AuthPw:)

[[#submission]]
----
(:sectiontitle:)News Submission Form(:sectiontitleend:)
newssubmissionform
Note: Placement of an item inside AINews is dependent on that item's tags. Specifically, if an item is tagged with 'video' or if it is in the AIVideos/ page group, it will get placed in the Videos section. If an item is tagged with 'audio' or if it is in the AIAudio/ page group, it will get placed in the Audio section. Otherwise it will get placed in the general news headlines section. Tags also determine which RSS feeds the item goes in. For example, an item tagged with "speech" will get inserted into the "speech" RSS feed.
(:ifend:)
>><<(:videostitleend:)

        """
        pmwiki_output += footer
        pmwiki_output_norater += footer
        savefile("output/pmwiki_output.txt", pmwiki_output.encode('utf-8'))
        savefile("output/pmwiki_output_norater.txt", pmwiki_output_norater.encode('utf-8'))
        
        
        # Generate the metadata PmWiki page for every AIArticles
        
        urlids_output = ""
        for news in self.topnews:
            urlids_output += str(news['urlid']) +'\n'
            output = "(:description %s :) [[<<]]\n" % news['desc']
            output += """(:table:)
(:cellnr:) Title:
(:cell:) %%newwin%%[[%s| '''%s''']]
(:cellnr:) Description:
(:cell:) %s
(:cellnr:) Author:
(:cell:)
(:cellnr:) Orig. Date:
(:cell:) %s
(:cellnr:) Source:
(:cell:) %s
(:cellnr:) Subject:
(:cell:) %s
(:cellnr:) Contributor:
(:cell:) NewsFinder
(:cellnr:) Comments:
(:cell:)
(:cellnr:) Type:
(:cell:) Text
(:cellnr:) Language:
(:cell:) English
(:cellnr:) Format:
(:cell:) html
(:cellnr:) Last Edit:
(:cell:)  
(:tableend:)
(:collections :) brokenlinkform:brokenlink""" \
                % (news['url'], news['title'], news['desc'], news['pubdate'].strftime("%B %d, %Y"), news['publisher'], news['topic'])
            savefile("output/aiarticles/%d" % news['urlid'], output.encode('utf-8'))
        savefile("output/urlids_output.txt", urlids_output)
                            
        
        # Generate monthly summary in HTML code
        # Read-in all pkl output in this month from monthly directory
       
        year_str = self.today.strftime("%Y")
        month_str = self.today.strftime("%B")
        output = """<html><!-- InstanceBegin template="/Templates/TempCC.dwt" codeOutsideHTMLIsLocked="false" -->
<head>
<link rel="shortcut icon" href="http://www.aaai.org/AITopics/assets/Site%20Art/icon.gif"  type="image/gif">
<!-- #BeginEditable "doctitle" --> 
<title>Year """+year_str+" News Archive: "+month_str+"""</title>
<!-- #EndEditable --> 
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<meta name="keywords" content="AI, artificial intelligence, AAAI, Association for the Advancement of Artificial Intelligence, formerly American Association for Artificial Intelligence, AI Topics, pathfinder, computer science, cognitive science, robots, agents, games, puzzles, expert systems, natural language, LISP, history, philosophy, bibliography, news, science fiction, smart rooms, vision, speech, machine learning, chess, cartoons, toons, glossary, education, intelligent tutoring, reasoning, inference, logic, representation, ontology, turing, resources, teacher, educator, classroom, faqs, space, medicine, law, applications, overview, interface, systems">
<meta name="description" content="AI Topics provides basic, understandable information and helpful resources concerning artificial intelligence, with an emphasis on material available online. ">
<!-- InstanceParam name="OptionalRegion1" type="boolean" value="true" -->
<!-- Google Analytics -->
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
try {
var pageTracker = _gat._getTracker("UA-11601719-1");
pageTracker._trackPageview();
} catch(err) {}
</script>
</head>

<body link="#3333FF" vlink="#006600" alink="#FF6633">
<table width="95%" border="0" cellspacing="0" cellpadding="0" height="231">
  <tr> 
    <td width="2%" height="80" valign="middle" align="center"> 
      <div align="center"><a name="up"></a></div></td>
    <td height="80" colspan="2"> <div align="center"><font face="Arial" size="4"><!-- #BeginEditable "BANNER" --><font size="4" face="Arial"><b>Year """ + year_str + """ Archive of AI<i> in the news</i> articles<br>
        </b> <font size="3">-- """ + month_str + """ --</font></font><!-- #EndEditable --></font><br /><font face=Arial size="2">(a subtopic of <a href="http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/AINews">AI<i> in the 
        news</i></a>)</font></div><br /><br /></td> <td width="26%" height="80" align="right" valign="top"><font size="3" face="Arial"><a href="http://www.aaai.org/AITopics/">AI Topics Home</a></font>&nbsp;&nbsp;</td>
  </tr>
  <tr> 
    <td width="2%" height="144" valign="bottom"> &nbsp; 
      <div align="left"></div></td>
    <td bgcolor="#FFFFFF" valign="top" colspan="3"><!-- #BeginEditable "text" --> 
      <p><font size="3" face="Comic Sans MS"><a name="listtop"></a><a name="aialert"></a><font face="Arial">&lt;&lt; 
        <b><a href="#head">Headlines</a></b> are listed according to date posted 
        &lt;-&gt; <b><a href="#art">Articles</a></b> are organized by date published 
        &gt;&gt;</font></font> <font face="Arial"><a name="head"></a> </font></p>

      <ul>"""
        monthlynews = []
        i = 0
        for infile in glob( path.join("output/monthly/"+self.today.strftime("%Y-%m"), '*') ):
            currnews = loadpickle("output/topnews.pkl")
            monthlynews += currnews
            output += """<li><font size="2" face="Arial"><strong>%s articles</strong></font> <font size="2" face="Arial"><strong>posted during the week of %s %s</strong> <strong>%s </strong>""" % (month_str, month_str, path.basename(infile), year_str)
            for news in currnews:
                output += """ | <a href="#%d">%s</a> """ % (i, news['title'])
                i += 1
            output += "</font></li>\n\n"
        output += """</ul>
      <p><font face="Arial"><strong><font size="3"><a name="art"></a>Articles</font></strong></font></p>"""
        for i, news in enumerate(monthlynews):
            output += """<p><font size="3" face="Arial"><a name="%d"></a>%s: <a href="%s">%s</a>. %s. &quot;%s&quot;<br>
&gt;&gt;&gt; <a href="%s">%s</a><br>

<font size="3" face="Arial"><i>-&gt; <a href="#listtop">back to headlines</a></i></font> </font></p>""" % (i, news['pubdate'].strftime("%B %d, %Y"), news['url'], news['title'], news['publisher'], news['desc'], aitopic_urls[self.topicids[news['topic']]], news['topic'])
        output += """
         <!-- #EndEditable -->
      <table width="100%">
        <tr>
          <td width="50%">
            <div align="center"><a href="http://www.aaai.org/AITopics/pmwiki/pmwiki.php/AITopics/Notices#fairuse"><font face="Arial">Fair Use Notice</font></a></div>
          </td>

          <td width="50%">
<div align="center">&nbsp;&nbsp;<font face=Arial><a href="http://www.aaai.org/AITopics/html/notices.html#copy">&copy; 2000 - """+ year_str + """ by AAAI</a></font></div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>

<!-- InstanceEnd --></html>
""" 
        savefile("../../html/archive"+year_str+self.today.strftime("%m")+".html", output.encode('utf-8'))
        
        
    def publish_email(self):
        """
        Call AINewsEmail.php to send email through PHP Mail Server
        """
        cmd = 'php AINewsEmail.php'
        Popen(cmd, shell = True, stdout = PIPE).communicate()
        
        self.publish_email_semiauto()
        
    def publish_email_semiauto(self):
        """
        Create an AINewsSemiAutoEmail.html file for admin to click and semi-auto
        send it to the subscriber list.
        """
        semiauto = """
        <html>
        <body>
        <h1>AI Alert - SemiAuto Sender</h1>
        <form action="http://aaai.org/cgi-dada/mail.cgi?flavor=send_email" method='post'>
        <!-- <form action="welcome.php" method="post"> -->
        <input type='hidden' name='f' value='send_email' />
        <input type='hidden' name='process' value='true' />
        <input type='hidden' name='admin_list' value='alert' />
        <input type='hidden' name='message_subject' value="%s" />
        <input type='hidden' name='email_format' value='HTML' />
        <textarea type='hidden' name="text_message_body">%s</textarea>
        <input type='submit' value='Submit Mailing List Message' />
        </form>
        </body>
        </html>
        """ % ("AI Alert - "+str(self.today.strftime("%B %d, %Y")), self.semiauto_email_output)
        savefile("../../html/semiauto_email.html", semiauto.encode('utf-8'))

    def publish_email_daily(self):
        """
        Call AINewsEmailDaily.php to send email through PHP Mail Server by daily
        for testing purpose.
        """
        cmd = 'php AINewsEmailDaily.php'
        Popen(cmd, shell = True, stdout = PIPE).communicate()

    def publish_pmwiki(self):
        """
        Call AINewsPmwiki.php to publish latest news to AAAI Pmwiki website.
        """
        cmd = 'php AINewsPmwiki.php'
        Popen(cmd, shell = True, stdout = PIPE).communicate()
        
    def publish_pmwiki_daily(self):
        """
        Call AINewsPmwikiDaily.php to publish latest news to AAAI Pmwiki website
        for testing purpose.
        """
        cmd = 'php AINewsPmwikiDaily.php'
        Popen(cmd, shell = True, stdout = PIPE).communicate()
        
    def update_rss(self):
        rssitems = []
        # insert latest news into rssitems
        for news in self.topnews:
            rssitems.append(PyRSS2Gen.RSSItem(
                            title = news['title'],
                            link = news['url'],
                            description = news['desc'],
                            guid = PyRSS2Gen.Guid(news['url']),
                            pubDate = datetime(news['pubdate'].year, \
                                news['pubdate'].month, news['pubdate'].day)
                            ))
            
        rssfile = "../../xml/rss/news.xml"
        publish_rss(rssfile, rssitems)
        
        
        topicrsses = ['overview', 'agent', 'apps', 'cogsci', 'edu', 'ethsoc', 
            'game', 'hist', 'interf', 'ml', 'nlp', 'phil', 'reason',
             'rep', 'robot', 'scifi', 'speech', 'systems',  'vision']
        topicitems = []
        for i in range(len(topicrsses)): topicitems.append([])
        for news in self.topnews:
            topicid = self.topicids[news['topic']]
            topicitems[topicid].append(PyRSS2Gen.RSSItem(
                                title = news['title'],
                                link = news['url'],
                                description = news['desc'],
                                guid = PyRSS2Gen.Guid(news['url']),
                                pubDate = datetime(news['pubdate'].year, \
                                    news['pubdate'].month, news['pubdate'].day)
                                ))
            
        for i in range(len(topicrsses)):
            rssfile = "../../xml/rss/"+topicrsses[i]+'.xml'
            if len(topicitems[i]) != 0:
                publish_rss(rssfile, topicitems[i])
        
    
def publish_rss(rssfile, rssitems):
    now = datetime.now()
    rss_begindate = now - timedelta(days = 60)
    
    newstitleset = set()
    f = feedparser.parse(rssfile)
    # remove out-of-date news and add rest of the news into rssitems
    for entry in f.entries:
        if not entry.has_key('updated_parsed'): continue
        d = datetime(entry.date_parsed[0], \
                       entry.date_parsed[1], entry.date_parsed[2])
        if d > now or d < rss_begindate: continue
        if entry.title in newstitleset: continue
        else: newstitleset.add(entry.title)
        rssitems.append( PyRSS2Gen.RSSItem(
                        title = entry.title,
                        link = entry.link,
                        description = entry.description,
                        guid = PyRSS2Gen.Guid(entry.link),
                        pubDate = d))
    
    # Use PyRSS2Gen to generate the output RSS    
    rss = PyRSS2Gen.RSS2(
        title = f.channel.title,
        link = f.channel.link,
        description = f.channel.description,
        lastBuildDate = now,
        language = 'en-us',
        webMaster = "aitopics08@aaai.org (AI Topics)",
        items = rssitems)
    
    rss.write_xml(open(rssfile, "w"))
        
