# NewsFinder

Full details of this software can be found at
[the AITopics wiki](http://aaai.org/AITopics/AINewsProcedure).

The main script, `AINews.py`, performs the
training/crawling/publishing process. The script can be called with
one of three arguments:

<pre>
python AINews.py crawl
</pre>

This crawls the sources list (database table `sources`) and stores its
results back into the database (table `urllist`).

<pre>
python AINews.py publish
</pre>

This grabs the articles that have been crawled but not yet processed,
filters stories based on relevance, and publishes the resutls as wiki
pages, email, and RSS feeds.

## Installation

NewsFinder is primarily coded in Python and requires the following libraries:

  - MySQL Python bindings (MySQLdb)
  - [libsvm2](http://www.csie.ntu.edu.tw/~cjlin/libsvm/)
  - [Justext](http://code.google.com/p/justext/)
  - [cheetah](http://www.cheetahtemplate.org/)
  - [nltk](http://www.nltk.org/)
  - [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/)
  - [PyRSS2Gen](http://www.dalkescientific.com/Python/PyRSS2Gen.html)
  - [feedparser](http://www.feedparser.org/)
  
"Installation" of AINews should only involve downloading the code in
this repository. Assuming Python includes the AINews code in its path,
execution of AINews should be as simple as running `python AINews.py`

There are various supplementary files that AINews expects; these
involve publishing the news into PmWiki format and generating an
email-formatted output. These files can be obtained from another
repository:
[AINewsSupplementary](https://github.com/joshuaeckroth/AINewsSupplementary)

In our working configuration, we have a directory in our home called
`NewsFinder`. In this directory are the AINewsSupplementary
directories (e.g. `templates`, `resource`, etc.). The AINews code
found in this repository is stored in a `code` directory in the main
`NewsFinder` folder. In any event, the `paths.ini` file (in the
`config` directory of this project) can be modified to point to
whereever you keep your files.

## Database

Look at `tables.sql` to create tables needed by NewsFinder.

## News sources

Sources are specified in the `sources` table of the database. A source
has the following properties: URL, parser identifier, description,
status, and relevance. The URL points to either an RSS feed or a
search results page that is to be parsed. The parser identifier is
composed of two parts separated by `::` -- the first part is the
publisher name, the second part is the type (e.g. `rss`); the parser
identifer (both parts) is used in `AINewsSourceParser.py` to determine
how the URL will be processed. If you wish to crawl a news source not
yet represented in `AINewsSourceParser.py`, you may have to write a
new parser (see the file for examples). The description of the source
is just helpful text to disambiguate among different search terms used
on the same publisher (e.g. all the different Google News
searches). The description is not used by the AINews code. Finally,
status is a boolean value (1 or 0) indicating whether this source
should be crawled, and relevance is a ranking (higher = better) of how
relevant or credible is the source. Stories from more relevant sources
are more likely to be published.

## Configuration

All configuration is provided in the `config/*.ini` files:

  - `config.ini` has miscellaneous configuration options, described in
    the file
  - `db.ini` has database connectivity information (host, username,
    password, etc.)
  - `paths.ini` stores the paths of various data and output
    directories used by AINews. This file allows you to store data and
    output in whatever way makes sense for a particular installation
    (for example, data files should be outside of a webserver root)

Make a copy of the `.ini.sample` files (rename to `.ini`) to build
your own configuration.

## Train

<pre>
python AINews.py train
</pre>

The trainer collects user ratings and finds the best support vector
machines to categorize the articles and select which are relevant to
AINews readers. Output is saved to the `svm_data` path (defined in
`config/paths.ini`).

# Authors

The most recent version (as of this writing) of NewsFinder was written
by [Joshua Eckroth](http://aaai.org/AITopics/Profiles/Jeckroth). The
prior iteration was written by
[Liang Dong](http://aaai.org/AITopics/Profiles/Ldong). Before that,
NewsFinder was coded by
[Tom Charytoniuk](http://aaai.org/AITopics/Profiles/Tcharytoniuk). The
project has been supervised by
[Bruce Buchanan](http://aaai.org/AITopics/Profiles/Bgbuchanan) and
[Reid Smith](http://aaai.org/AITopics/Profiles/Rgsmith).

# Publications

The NewsFinder software is been documented in the following
publications:

L. Dong, R. G. Smith and
B.G. Buchanan. [NewsFinder: Automating an Artificial Intelligence News Service](http://www.aaai.org/AITopics/articles&columns/NewsFinder2011.pdf). *Twenty-Third
IAAI Conference on Innovative Applications of Artificial Intelligence
(IAAI11)*, July, 2011.

L. Dong, R. G. Smith and
B.G. Buchanan. [Automating the Selection of Stories for AI in the News](http://www.aaai.org/AITopics/assets/PDF/NewsFinder_IEA-AIE_2011.pdf). *Twenty-fourth
International Conference on Industrial, Engineering and Other
Applications of Applied Intelligent Systems (IEA/AIE 2011)*, June,
2011.

# License

Copyright (c) 2011 by the Association for the Advancement of
Artificial Intelligence. This program and parts of it may be used and
distributed without charge for non-commercial purposes as long as this
notice is included.
