# AINews

The main script, `AINews.py`, accepts 

The main script, `AINews.py`, performs the training/crawling/publishing
process. The script can be called with the `all` option to perform all steps:

<pre>
python AINews.py all
</pre>

Or, one of `train`, `crawl`, `rank`, or `publish` can be used to
execute just one of the subprocesses, e.g.:

<pre>
python AINews.py crawl
</pre>

## Database

Look at `tables.sql` to create tables needed by AINews. The table-creation
code in that file is documented as well.

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
rank news articles as irrelevant, somewhat relevant, or relevant. Output is
saved to the `svm_data` path (defined in `config/paths.ini`).

## Crawl

The crawler can be invoked by:

<pre>
python AINews.py crawl
</pre>

The crawler will read the `sources` table in the database and crawl
each source. In the `sources` table, each source has a parser associated with
it. You can add new parsers (and thus new sources) by adding to
`AINewsSourceParser.py`.

Articles are processed as they are crawled. Results are stored in the `urllist`
table. Also, article descriptions are stored in the `news_data/desc/`
directory, article text is stored in `news_data/text/`, and article metadata
(title, publication date, topic, etc.) is stored in `news_data/meta/`; in each
case, the urlid (as found from the `urllist` table) is the name of the file,
and the extension is `.pkl` (Python "pickle" file).

## Rank

The ranker finds recent articles saved into the database (from the crawler, in
the table `urllist`) and chooses the highest scoring news, while also trying to
choose news from multiple categories. The "top news" is saved into the `output`
folder (from `paths.ini`) in a Python "pickle" file called `topnews.pkl`.  This
is the file that the publisher (described below) uses to generate HTML files
and RSS feeds for the news.

## Publish

The publisher reads the news articles stored in `topnews.pkl` (see "Rank"
above), and writes HTML and RSS files with the appropriate formatting. The
formats are given by Cheetah templates (the `compiled` path, in the section
`templates`, in `config/paths.ini`). Pmwiki is assumed to be the content
management system providing the AINews website, so Pmwiki-styled output is
produced by the publisher, as well as RSS feeds and an email designed for
sending to the AIAlert mailing list.

# Classifier

The classifier is not executed by `AINews.py`. Rather, the classifier is used
by the crawling process to classifier the news. The classifier can be trained
and evaluated by running the `AINewsCentroidClassifier.py` script, as described
below.

## Evaluating the classifier

The classifier can be trained/evaluated on a file-based corpus (described in
the README.corpus file) or a database corpus (essentially described by the
`cat_corpus` and `cat_corpus_cats` tables in `tables.sql`). A file-based
corpus can be indicated by the format `file:X` where `X` is a corpus name. The
corpus is read from the file `corpus_other/X.mat` and related files
(`X.mat.clabel` and `X.mat.rlabel`). The directory `corpus_other` can be
specified in `config/paths.ini`.

<pre>
python AINewsCentroidClassifier.py evaluate file:oh10
</pre>

The other option is a database corpus. The `db:X:Y` specification format is as
follows: `X` is the table with corpus articles (format follows `cat_corpus`
table described in `tables.sql`); `Y` is the table with corpus article
categories (`cat_corpus_cats` described in `tables.sql`).

<pre>
python AINewsCentroidClassifier.py evaluate db:cat_corpus:cat_corpus_cats
</pre>

You will probably want to save the output (redirect stdout) to a file.

## Filtering results

The classifier evaluator may print a lot of poor results, with the good results
mixed in and thus hard to find. The script `process-results.pl` may be helpful
here. Edit the script to filter only the data that is meaningful, then execute
as follows:

<pre>
perl process-results.pl &lt; evaluator-output.txt
</pre>


## Exporting the corpus dissimilarity matrix

<pre>
python CorpusExport.py file:oh10 > corpus-oh10.csv
</pre>


Then you can graph these dissimilarities using R:

<pre>
Rscript corpus-mds.r corpus-oh10
</pre>

That command will produce the graphs `corpus-oh10-mds.png` and
`corpus-oh10-mds-faceted.png`.


