# NewsFinder

Full details of this software can be found at [the AITopics wiki](http://aaai.org/AITopics/AINewsProcedure).

The main script, `AINews.py`, performs the training/crawling/publishing
process. The script can be called with one of three arguments:

<pre>
python AINews.py crawl
</pre>

This crawls the sources list (database table `sources`) and stores its results
back into the database (table `urllist`).

<pre>
python AINews.py publish
</pre>

This finds the articles that have been crawled but not yet processed, filters
stories based on relevance, and publishes the resutls as wiki pages, email, and
RSS feeds.

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

## Database

Look at `tables.sql` to create tables needed by NewsFinder.

## Configuration

All configuration is provided in the `config/*.ini` files:

  - `config.ini` has miscellaneous configuration options, described in the file
  - `db.ini` has database connectivity information (host, username, password,
    etc.)
  - `paths.ini` stores the paths of various data and output directories used by
    AINews. This file allows you to store data and output in whatever way makes
    sense for a particular installation (for example, data files should be outside
    of a webserver root)

Make a copy of the `.ini.sample` files (rename to `.ini`) to build your own
configuration.

## Train

The trainer collects user ratings and finds the best support vector machines to
categorize the articles and select which are relevant to AINews readers. Output
is saved to the `svm_data` path (defined in `config/paths.ini`).
