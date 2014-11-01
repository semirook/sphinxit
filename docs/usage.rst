.. _usage:

Usage
=====

Make sure you have `Sphinx <http://sphinxsearch.com/>`_ itself up and running. 
If you have no idea what to do, read it's own `official docs <http://sphinxsearch.com/docs/current.html>`_. 
Maybe, :ref:`preparation` tutorial will be useful for you too.

So, you have some Python application and just want to start use Sphinx in it? 
Some kind of filtered fulltext queries, maybe? Snippets? I know that feel :)
And Sphinxit was created exactly for that, as a thin layer between your Python app and powerful 
Sphinx search engine.


Configuration
-------------

First of all - create Sphinxit config class::

    class SphinxitConfig(object):
        DEBUG = True
        WITH_META = True
        WITH_STATUS = True
        POOL_SIZE = 5
        SQL_ENGINE = 'oursql'
        SEARCHD_CONNECTION = {
            'host': '127.0.0.1',
            'port': 9306,
        }

Actually, you don't have to write this class from scratch, because there is
BaseSearchConfig class in ``sphinxit.core.helpers`` module::

    from sphinxit.core.helpers import BaseSearchConfig

    class SphinxitConfig(BaseSearchConfig):
        WITH_STATUS = False 

The class from above does the same but with :attr:`WITH_STATUS` False value (not everyone needs it).
By the way, :attr:`WITH_STATUS` makes additional `SHOW STATUS <http://sphinxsearch.com/docs/current.html#sphinxql-show-status>`_ 
subquery for each of yours search query.

The :attr:`DEBUG` attribute sets the level of verbosity and behavior. If it's True, illegal arguments 
for search methods will raise exceptions with useful hints about what's wrong and how you can fix it. 
Don't panic, it's normal and you have to know what has to be fixed to process correct query.
If it's False, and it should be so in production, illegal filters, options, sortings, etc. 
will be ignored. Sphinxit will try to complete the query correctly, without broken parts.

:attr:`WITH_META` sets to return some useful stats (`SHOW META <http://sphinxsearch.com/docs/current.html#sphinxql-show-meta>`_ subquery)
with your search results. If you don't care - turn it off, set to False.

The :attr:`SQL_ENGINE` allow you to select engine for sql client. Supported options: 'oursql' (default) and 'mysqldb'.

The :attr:`SEARCHD_CONNECTION` attribute sets connection settings for the Sphinx's ``searchd`` daemon. 
Change the host and port values if they differ from defaults, check your ``sphinx.conf``.

Since 0.3.1 version, Sphinxit has a connector with simple connection pool, to reduce connections opening/closing overhead.
You can tune how much connections will be preopen, how much ``searchd`` instances will be run for queries processing
with :attr:`POOL_SIZE` attribute value. Default is 5.


Your first query
----------------

Let's define some conventions::

    # Import path, I'll write it once, before new class or helper usage
    from sphinxit.core.processor import Search

    # Base query that will be used in further examples
    search_query = Search(indexes=['company'], config=SphinxitConfig)

    # Internally translates into valid SphinxQL query:
    # SphinxQL> SELECT * FROM company


You can use Sphinxit with any Sphinx configuration you already have. Set a list of indexes
and pass Sphinxit config as above to start make queries. 

The main class with set of special methods is :class:`Search`::

    from sphinxit.core.processor import Search

    search_query = Search(indexes=['company'], config=SphinxitConfig)
    search_query = search_query.match('fulltext query')

    # SphinxQL> SELECT * FROM company WHERE MATCH('fulltext query')

Every search method except the :meth:`ask()` is chainable.

The :meth:`ask()` method explicitly fetches all results from the ``searchd``::

    search_result = search_query.ask()

The ``search_result`` is a dict with key ``result`` (by default). Like this::

    {
        u'result': {
            u'items': [
                {
                    'id': 5015L, 
                    'name': u'Doc 1',
                    'date_created': 2008L, 
                }, 
                {
                    'id': 25502L,
                    'name': u'Doc 2',
                    'date_created': 2009L, 
                },
                ...
            ],
            u'meta': {
                u'total': u'16',
                u'total_found': u'16',
                u'docs[0]': u'16', 
                u'time': u'0.000', 
                u'hits[0]': u'16', 
                u'keyword[0]': u'doc'
            }
        }
    }

It can seem strange, result dict with one key... You'll see later in subqueries examples why it is so.

The :meth:`match()` method was used for fulltext search and the :meth:`ask()` method for search processing.
Remember that :meth:`ask()` is the end point of your query.

This query gets all of the document attributes that were specified in your ``sphinx.conf``.
If you want to set some explicit list of attributes to get only them, use the :meth:`select()` method::

    search_query = search_query.select('id', 'name')
    # SphinxQL> SELECT id, name FROM company WHERE MATCH('fulltext query')

2 moments here: 

* the query chain is not mutable inplace;
* the order of method calls doesn't matter.

Also, you can set aliases for your attributes::

    search_query = search_query.select('id', ('name', 'title'))
    # SphinxQL> SELECT id, name AS title FROM company

or, alternative form::

    search_query = search_query.select(id, name='title')
    # SphinxQL> SELECT id, name AS title FROM company


Fulltext searching
------------------

The :meth:`match()` method provides proper chars escaping, usually it's what you need. 
But you may want to make some `raw` query too. Use :meth:`match()`
without escaping by providing extra argument :attr:`raw=True`. Note the difference::

    search_query = search_query.match('@name query for search + "exact phrase"')
    # SphinxQL> SELECT * FROM company WHERE MATCH('\@name query for search \\+ \"exact phrase\"')

and as a "raw" query::

    search_query = search_query.match('@name query for search + "exact phrase"', raw=True)
    # SphinxQL> SELECT * FROM company WHERE MATCH('@name query for search + "exact phrase"')


.. note::
    You have to be very careful with fulltext queries from the outside in the raw mode, 
    they can contain special chars and you have to escape them manually!


Filtering
---------

Sphinxit works without data schema (like ORMs), so there is special syntax to filter query by attributes:

==================================== =================================
Sphinxit                             SphinxQL
==================================== =================================
``attr__eq = value``                 ``attr = value``
``attr__neq = value``                ``attr != value``
``attr__gt = value``                 ``attr > value``
``attr__gte = value``                ``attr >= value``
``attr__lt = value``                 ``attr < value``
``attr__lte = value``                ``attr <= value``
``attr__in = [value, value, ...]``   ``attr IN (value, value, ...)``
``attr__between = [value, value]``   ``attr BETWEEN (value, value)``
==================================== =================================

Some examples::

    search_query = search_query.filter(id__gt=42)
    # SphinxQL> SELECT * FROM company WHERE id > 42

    search_query = search_query.filter(id__between=[100, 200], id__in=[50,51,52])
    # SphinxQL> SELECT * FROM company WHERE id BETWEEN 100 AND 200 AND id IN (50, 51, 52)

    search_query = search_query.filter(id__gt=42).filter(id__between=[100, 200], id__in=[50,51,52])
    # SphinxQL> SELECT * FROM company WHERE id > 42 AND id BETWEEN 100 AND 200 AND id IN (50, 51, 52)

Sure, you can combine them as you wish.

Note, that you can't use string attributes in filter clauses. It's Sphinx engine limitation. Integers, floats, datetime - you're welcome::

    # will raise an exception, use match() for that
    search_query = search_query.filter(name__eq="Semirook")

Sphinx uses UNIX_TIMESTAMP to work with data, so Sphinxit converts date and datetime to UNIX_TIMESTAMP implicitly::

    search_query = search_query.filter(date_created__lt=datetime.today())
    # SphinxQL> SELECT * FROM company WHERE date_created < 1372539600


OR objects
++++++++++

Sphinx joins your filters with AND, but you may want to join them with OR logic. 
There is workaround for that case and to make it simple to use, Sphinxit provides special OR objects::
    
    from sphinxit.core.nodes import OR

Simple example::

    search_query = search_query.filter(OR(id__gte=100, id__eq=1))
    # SphinxQL> SELECT *, (id>=100 OR id=1) AS cnd FROM company WHERE cnd>0

More complex, with OR expressions joins::

    search_query = search_query.filter(
        OR(id__gte=100, id__eq=1) & OR(
            date_created__eq=datetime.today(),
            date_created__lte=datetime.today() - datetime.timedelta(days=3)
        )
    )
    # SphinxQL> SELECT *, \
    #           (id>=100 OR id=1) AND (date_created=1372798800 OR date_created<=1372539600) AS cnd \
    #           FROM index WHERE cnd>0

You can combine OR expressions via ``&`` or ``|`` (means ``AND`` and ``OR`` groups concatanation)::

    search_query = search_query.filter(
        OR(id__gte=100, id__eq=1) | OR(id__eq=42, id__lt=24, date_created__lt=datetime.today())
    )
    # SphinxQL> SELECT *, \
    #           (id>=100 OR id=1) OR (id=42 OR id<24 OR date_created=1372798800) AS cnd \
    #           FROM index WHERE cnd>0


Single OR expression group can contain as much filters as you need. 

.. note::
   __between, __in, __neq filtering is not allowed in OR expressions.


Grouping
--------

Aggregation is for some kind of data group processing. You can group search results with
:meth:`group_by()` method, by some field, and make some aggregation operation, like a counting::

    search_query = search_query.match('Yandex').select('date_created', Count()).group_by('date_created')
    # SphinxQL> SELECT date_created, COUNT(*) as num FROM company WHERE MATCH('Yandex') GROUP BY date_created

This expression will group search results by the field ``date_created`` and will count how much items we have in these groups, with special :class:`Count()` aggregation object. 

The raw result of this query is something like this::

    +--------------+------+
    | date_created | num  |
    +--------------+------+
    |         2011 |   12 |
    |         2009 |    1 |
    |         2010 |    5 |
    |         2012 |   26 |
    |         2013 |    8 |
    +--------------+------+
    5 rows in set (0.00 sec)

Aggregation objects
+++++++++++++++++++

The most popular functions are implemented. You can find them all in the ``sphinxit.core.nodes`` module::

    from sphinxit.core.nodes import Avg, Min, Max, Sum, Count

All of them take two arguments - name of some field to aggregate and optional alias (for the :class:`Count` object, name is also optional)::

    search_query = (
        search_query
        .select('id', 'name', Count('name', 'company_name'))
        .group_by('name')
        .order_by('company_name', 'desc')
    )
    # SphinxQL> SELECT id, name, COUNT(DISTINCT name) AS company_name  \
    #           FROM company 
    #           GROUP BY name 
    #           ORDER BY company_name DESC

Note the difference between the forms of released Counts. If you pass a name of a field as the first attribute,
the Count is ``DISTINCT``. Use named attribute :attr:`alias` explicitly to save the star syntax::

    search_query = search_query.select('date_created', Count(alias='date_alias')).group_by('date_created')
    # SphinxQL> SELECT date_created, COUNT(*) AS date_alias FROM company GROUP BY date_created

Try to experiment with this.

Limit
-----

Sure, you can specify how much results you want to get, the size of necessary limit. 
There is :meth:`limit()` method for that with two arguments - ``offset`` and ``limit``::

    search_query = search_query.limit(0, 100)
    # SphinxQL> SELECT * FROM company LIMIT 0, 100

.. note::
   Implicit Sphinx limit is **20**


Ordering
--------

Just specify the field you want to sort by and the direction of sorting: 
``asc`` or ``desc`` (case insensitive)::

    search_query = search_query.match('Yandex').limit(0, 100).order_by('name', 'desc')
    # SphinxQL> SELECT * FROM company ORDER BY name DESC LIMIT 0, 100 

Options
-------

Sphinxit knows about Sphinx's `OPTION clause <http://sphinxsearch.com/docs/current.html#sphinxql-select>`_
and you can work with almost all of them:

========================= ======================================================================== ==============
Option                    Description                                                              Param type
========================= ======================================================================== ==============
``ranker``                Any of 'proximity_bm25', 'bm25', 'none', 'wordcount', 'proximity',       string
                          'matchany', 'fieldmask', 'sph04' or 'expr'. See the table below.
``max_matches``           Integer (per-query max matches value).                                   integer
``cutoff``                Integer (max found matches threshold).                                   integer
``max_query_time``        Integer (max search time threshold, msec).                               integer
``retry_count``           Integer (distributed retries count).
``retry_delay``           Integer (distributed retry delay, msec).                                 integer
``field_weights``         A named integer list (per-field user weights for ranking).               dict
``index_weights``         A named integer list (per-index user weights for ranking).               dict
``reverse_scan``          0 or 1, lets you control the order in which full-scan query processes    bool
                          the rows.
``comment``               String, user comment that gets copied to a query log file.               string
========================= ======================================================================== ==============

Combine them to tune up your search mechanism::

    search_query = (
        search_query
        .match('Yandex')
        .select('id', 'name')
        .options(
            ranker='proximity_bm25',
            max_matches=100,
            field_weights={'name': 100, 'description': 80},
        )
        .order_by('name', 'desc')
    )
    # SphinxQL> SELECT id, name \
    #           FROM company
    #           WHERE MATCH('Yandex') 
    #           ORDER BY name 
    #           DESC OPTION ranker=proximity_bm25, max_matches=100, field_weights=(name=100, description=80)

From Sphinx docs: 

    | Ranking (aka weighting) of the search results can be defined as a process of computing a so-called 
    | relevance (aka weight) for every given matched document with regards to a given query that matched it. 
    | So relevance is in the end just a number attached to every document that estimates how relevant the document 
    | is to the query. Search results can then be sorted based on this number and/or some additional parameters, 
    | so that the most sought after results would come up higher on the results page.
    
And valid rankers are:

========================= ======================================================================== ================
Ranker                    Description                                                              Sphinx ver.
========================= ======================================================================== ================
``proximity_bm25``        The default ranking mode that uses and combines both phrase proximity    ALL 
                          and BM25 ranking.
``bm25``                  Statistical ranking mode which uses BM25 ranking only (similar to most   ALL
                          other full-text engines). This mode is faster but may result in worse 
                          quality on queries which contain more than 1 keyword.
``wordcount``             Ranking by the keyword occurrences count. This ranker computes           ALL 
                          the per-field keyword occurrence counts, then multiplies them by field 
                          weights, and sums the resulting values.
``proximity``             Returns raw phrase proximity value as a result. This mode is internally  0.9.9-rc1
                          used to emulate SPH_MATCH_ALL queries.
``matchany``              Returns rank as it was computed in SPH_MATCH_ANY mode ealier, and is     0.9.9-rc1
                          internally used to emulate SPH_MATCH_ANY queries.
``fieldmask``             Returns a 32-bit mask with N-th bit corresponding to N-th fulltext       0.9.9-rc2
                          field, numbering from 0. The bit will only be set when the respective 
                          field has any keyword occurences satisfiying the query.
``sph04``                 Is generally based on the default SPH_RANK_PROXIMITY_BM25 ranker,        1.10-beta 
                          but additionally boosts the matches when they occur in the very 
                          beginning or the very end of a text field. Thus, if a field equals 
                          the exact query, SPH04 should rank it higher than a field that contains 
                          the exact query but is not equal to it. (For instance, when the query 
                          is "Hyde Park", a document entitled "Hyde Park" should be ranked higher 
                          than a one entitled "Hyde Park, London" or "The Hyde Park Cafe".)
``expr``                  Lets you specify the ranking formula in run time. It exposes a number    2.0.2-beta 
                          of internal text factors and lets you define how the final weight 
                          should be computed from those factors. You can find more details about 
                          its syntax and a reference available factors in a subsection below.
``none``                  No ranking mode. This mode is obviously the fastest. A weight of 1       ALL
                          is assigned to all matches. This is sometimes called boolean searching 
                          that just matches the documents but does not rank them.
========================= ======================================================================== ================

Read more about rankers `here <http://sphinxsearch.com/docs/current.html#weighting>`_.

Batch. Subqueries. Facets.
--------------------------

Since 0.3.1 Sphinxit version you can make subqueries. It can be very useful to process
several queries at a time with the same connection. It's more fast and efficient than
making series of separate queries. For example, you want to recieve fulltext query result
with different groupings but with the same base part::

    search_result_1 = search_query.match('Yandex').ask()
    search_result_2 = (
        search_query.match('Yandex')
        .select('date_created', Count())
        .group_by('date_created')
        .ask()
    )
    search_result_3 = (
        search_query.match('Yandex')
        .select('id', 'name', Count('name', 'company_name'))
        .group_by('name')
        .order_by('company_name', 'desc')
        .ask()
    )

You can rewrite queries from above as subqueries::

    search_query = search_query.match('Yandex').named('main_query')
    search_result = search_query.ask(
        subqueries=[
            (
                search_query.select('date_created', Count())
                .group_by('date_created')
                .named('date_group'),
            )
            (
                search_query.select('id', 'name', Count('name', 'company_name'))
                .group_by('name')
                .order_by('company_name', 'desc')
                .named('name_group')
            )
        ]
    )

And the result is more clean and convenient for postprocessing. 
Also, you can save several milliseconds on each subquery for free!

Note the new method :meth:`named()` here. It sets the name of the key in result data structure. In the first
example you'll get three separate dicts with search results. But in the second example with subqueries you'll
get one dict with key/value per each query::

    {
        u'main_query': {
            u'items': [
                {'date_created': 2011L, 'products': u'', 'id': 345060L, ...}, 
                {'date_created': 2009L, 'products': u'406,409,517', 'id': 78966L, ...}, 
                {'date_created': 2010L, 'products': u'349052', 'id': 97693L, ...},
                ...
            ],
            u'meta': {
                u'total': u'50', 
                u'total_found': u'50', 
                u'docs[0]': u'52', 
                u'time': u'0.000', 
                u'hits[0]': u'53', 
                u'keyword[0]': u'yandex'
            }
        },
        u'date_group': {
            u'items': [
                {'date_created': 2011L, 'num': 12L},
                {'date_created': 2009L, 'num': 1L}, 
                {'date_created': 2010L, 'num': 5L},
                {'date_created': 2012L, 'num': 26L},
                {'date_created': 2013L, 'num': 8L}
            ],
            u'meta': {
                u'total': u'5',
                u'total_found': u'5',
                u'docs[0]': u'52',
                u'time': u'0.000', 
                u'hits[0]': u'53',
                u'keyword[0]': u'yandex'
            }
        },
        u'name_group': {
            u'items': [
                {'company_name': 2L, 'id': 433302L, 'name': u'yandex'}, 
                {'company_name': 1L, 'id': 167334L, 'name': u'Yandex.ru'}, 
                {'company_name': 1L, 'id': 403574L, 'name': u'Yandex.ua'},
                ...
            ], 
            u'meta': {
                u'total': u'50', 
                u'total_found': u'50', 
                u'docs[0]': u'52',
                u'time': u'0.000', 
                u'hits[0]': u'53', 
                u'keyword[0]': u'yandex'
            }
        }
    }


Update syntax
-------------

Sphinxit supports UPDATE syntax for disk indexes. You can update
any value of any attribute except strings. The usage is quite simple::

    search = Search(['company'], config=SearchConfig)
    search = search.match('Yandex').update(products=(5,2)).filter(id__gt=1)
    # SphinxQL> UPDATE company SET products=(5,2) WHERE MATCH('Yandex') AND id>1

`TODO: Complete this chapter` 


Snippets
--------

There is special :class:`Snippet` class to provide `CALL SNIPPETS <http://sphinxsearch.com/docs/current.html#sphinxql-call-snippets>`_ syntax that is used for semi-automatic snippets creation.

The usage is similar to :class:`Search`, but set of methods is quit different.

* :meth:`from_data()` describes what text data should be used to process snippets.
* :meth:`for_query()` is for fulltext query, like :meth::`match()` method in :class:`Search`.
* :meth:`options()` supports all of the ``excert`` options from `Sphinx docs <http://sphinxsearch.com/docs/current.html#api-func-buildexcerpts>`_.

I hope it's clear how to use it from this snippet::

    snippets = (
        Snippet(index='company', config=SearchConfig)
        .for_query("Me amore")
        .from_data("amore mia")
        .options(before_match='<strong>', after_match='</strong>')
    )
    # SphinxQL> CALL SNIPPETS \
    #           ('amore mia', 'company', 'Me amore', '<strong>' AS before_match, '</strong>' AS after_match)

========================= ======================================================================== ================
Option                    Description                                                              Sphinx ver.
========================= ======================================================================== ================
``before_match``          A string to insert before a keyword match. Default is "<b>".             ALL
``after_match``           A string to insert after a keyword match. Default is "</b>".             ALL
``chunk_separator``       A string to insert between snippet chunks (passages).                    ALL
                          Default is " ... ". "
``limit``                 Maximum snippet size, in symbols (codepoints).                           ALL
                          Integer, default is 256.
``around``                How much words to pick around each matching keywords block.              ALL
                          Integer, default is 5.
``exact_phrase``          Whether to highlight exact query phrase matches only instead of          ALL
                          individual keywords. Boolean, default is false.
``use_boundaries``        Whether to additionaly break passages by phrase boundary characters,     ALL
                          as configured in index settings with phrase_boundary directive. 
                          Boolean, default is false.
``weight_order``          Whether to sort the extracted passages in order of relevance             ALL
                          (decreasing weight), or in order of appearance in the document 
                          (increasing position). Boolean, default is false.
``query_mode``            Whether to handle words as a query in extended syntax, or as a bag       1.10-beta
                          of words (default behavior). For instance, in query mode 
                          ("one two" | "three four") will only highlight and include those 
                          occurrences "one two" or "three four" when the two words from each pair 
                          are adjacent to each other. In default mode, any single occurrence of 
                          "one", "two", "three", or "four" would be highlighted. 
                          Boolean, default is false.
``force_all_words``       Ignores the snippet length limit until it includes all the keywords.     1.10-beta
                          Boolean, default is false.
``limit_passages``        Limits the maximum number of passages that can be included into          1.10-beta
                          the snippet. Integer, default is 0 (no limit).
``limit_words``           Limits the maximum number of words that can be included into             1.10-beta
                          the snippet. Note the limit applies to any words, and not just 
                          the matched keywords to highlight. For example, if we are highlighting 
                          "Mary" and a passage "Mary had a little lamb" is selected, then it 
                          contributes 5 words to this limit, not just 1. 
                          Integer, default is 0 (no limit).
``start_passage_id``      Specifies the starting value of %PASSAGE_ID% macro 
                          (that gets detected and expanded in before_match, after_match strings).  1.10-beta
                          Integer, default is 1.
``load_files``            Whether to handle $docs as data to extract snippets from                 1.10-beta
                          (default behavior), or to treat it as file names, and load data 
                          from specified files on the server side.
``load_files_scattered``  It works only with distributed snippets generation with remote agents.   2.0.2-beta
                          The source files for snippets could be distributed among different 
                          agents, and the main daemon will merge together all non-erroneous 
                          results. So, if one agent of the distributed index has 'file1.txt', 
                          another has 'file2.txt' and you call for the snippets with both these 
                          files, the sphinx will merge results from the agents together, 
                          so you will get the snippets from both 'file1.txt' and 'file2.txt'.
                          Boolean, default is false.
``html_strip_mode``       HTML stripping mode setting. Defaults to "index", which means that       1.10-beta 
                          index settings will be used. The other values are "none" and "strip",
                          that forcibly skip or apply stripping irregardless of index settings; 
                          and "retain", that retains HTML markup and protects it from 
                          highlighting. The "retain" mode can only be used when highlighting 
                          full documents and thus requires that no snippet size limits are set. 
                          String, allowed values are "none", "strip", "index", and "retain".
``allow_empty``           Allows empty string to be returned as highlighting result when           1.10-beta
                          a snippet could not be generated (no keywords match, or no passages 
                          fit the limit). By default, the beginning of original text would be 
                          returned instead of an empty string. Boolean, default is false.
``passage_boundary``      Ensures that passages do not cross a sentence, paragraph, or zone        2.0.1-beta
                          boundary (when used with an index that has the respective indexing 
                          settings enabled). String, allowed values are "sentence", "paragraph", 
                          and "zone".
``emit_zones``            Emits an HTML tag with an enclosing zone name before each passage.       2.0.1-beta
                          Boolean, default is false.
========================= ======================================================================== ================
