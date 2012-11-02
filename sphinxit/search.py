"""
    sphinxit.search
    ~~~~~~~~~~~~~~~

    Implements Sphinxit facade classes.

    :copyright: 2012 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import unicode_literals
from __future__ import absolute_import

try:
    import oursql
except ImportError:
    oursql = None

from .core.exceptions import SphinxQLSyntaxException, ImproperlyConfigured
from .core.processor import SphinxSearchBase
from .core.lexemes import SXQLSnippets


class SphinxConnector(object):
    """
    The start point of your new Sphinx-based search.
    Connects to the ``searchd`` via MySQL interface and this is how SphinxQL actually works,
    it speaks the same language as the MySQL network protocol. So make sure you have
    ``oursql`` package installed.

    :param host: ``searchd`` host IP address
    :param port: ``searchd`` port specified in your `sphinx.conf`

    Default host for every new connection is `127.0.0.1` and it's suitable in most cases.
    Default port is `9306`, compare it with specified one in your `sphinx.conf`::

        searchd {
            listen = 9306:mysql41
        }

    For example, standard usage is::

        Sphinxit = SphinxConnector()
        search_results = Sphinxit.Search('some_index').match('Hello!').process()

    You can have multiple connections to the ``searchd`` with different configurations
    via different ports if you whant to.

    `SphinxConnector` provides simple instance constructors for :class:`SphinxSearch` and :class:`SphinxSnippets`
    and binds proper lazy MySQL-connector to them::

        Sphinxit = SphinxConnector()
        search_results = Sphinxit.Search('some_index').match('Hello!').process()
        snippets_results = Sphinxit.Snippets('some_index', data='hello world', query='hello').process()
    """
    def __init__(self, **options):
        default_options = {'host': '127.0.0.1',
                           'port': 9306,
                           }

        self._conn_options = default_options
        self._conn_options.update(options)

    def get_connection(self):
        """
        Pay attention, I use `oursql`, not `mysqldb` as in the past.
        `oursql` supports Python 3, more powerful, tiny and well-documented.

        Connection is lazy, only :meth:`process` method calls it to execute some
        already prepared expressions.
        """
        if oursql is None:
            raise ImproperlyConfigured('Oursql library is needed to work with MySQL protocol.')

        try:
            return oursql.connect(**self._conn_options)
        except oursql.InterfaceError as e:
            errno, msg, extra = e
            raise SphinxQLSyntaxException(msg)

    def Search(self, *args):
        """
        :class:`SphinxSearch` instance constructor::

            Sphinxit = SphinxConnector()
            search_results = Sphinxit.Search('index', 'delta_index').match('Hello!').process()

        :param args: Sphinx index name or several indexes, separated with comma.
        """
        search_inst = SphinxSearch(*args)
        search_inst._bind_connection(self.get_connection)

        return search_inst

    def Snippets(self, index, data, query):
        """
        :class:`SphinxSnippets` instance constructor::

            Sphinxit = SphinxConnector()
            snippets_results = Sphinxit.Snippets('some_index', data='hello world', query='hello').process()

        :param index: Sphinx index name
        :param data: a string or a list of strings to extract snippets from
        :param query: the full-text query to build snippets for
        """
        search_inst = SphinxSnippets(index, data, query)
        search_inst._bind_connection(self.get_connection)

        return search_inst


class DBOperations(object):
    """Common set of methods for fetching index data by raw SphinxQL query"""

    def _bind_connection(self, conn):
        self._conn = conn
        return self

    def _get_connection(self):
        connection = getattr(self, '_conn', False)
        if not connection:
            raise ImproperlyConfigured('Cannot connect to Sphinx without proper connection.')

        return connection()

    def _get_result(self, sxql_query, with_meta=True, with_status=False):
        connection = self._get_connection()
        curs = connection.cursor(oursql.DictCursor)
        execute_query = lambda sxql_query: curs.execute(sxql_query, plain_query=True)
        normalize_meta = lambda result: dict([(x['Variable_name'], x['Value']) for x in result])
        try:
            execute_query(sxql_query)
            results = {'result': curs.fetchall()}

            if with_meta:
                execute_query('SHOW META')
                meta_result = curs.fetchall()
                results['meta'] = normalize_meta(meta_result)

            if with_status:
                execute_query('SHOW STATUS')
                status_result = curs.fetchall()
                results['status'] = normalize_meta(status_result)

            return results

        except oursql.ProgrammingError as e:
            errno, msg, extra = e
            raise SphinxQLSyntaxException(msg)

        finally:
            curs.close()


class SphinxSearch(SphinxSearchBase, DBOperations):
    """
    Implements SphinxQL `SELECT syntax <http://sphinxsearch.com/docs/current.html#sphinxql-select>`_
    and provides simple and clean way to make full-text queries, filtering, grouping, ordering search results etc.::

        Sphinxit = SphinxConnector()
        result = Sphinxit.Search('some_index').process()

    To make search by several indexes (you will, if you have main and delta indexes, for example), just separate
    their names with comma::

        Sphinxit= SphinxConnector()
        result = Sphinxit.Search('main_index', 'delta_index').process()

    .. note::
        :class:`SphinxSearch` needs connector to refer to ``searchd``, so you can't actually process
        query without initializing :class:`SphinxConnector` first.

    :param args: Sphinx index name or several indexes, separated with comma.
    """

    def process(self, with_meta=True, with_status=False):
        """
        Pay attention that query is not processed until you call the :meth:`process` method explicitly.
        You can dynamically construct as heavy queries as you want and process them only once when you need results,
        like this::

            ...
            query = Sphinxit.Search('main_index', 'delta_index').match('Good news')

            if self.request.GET.get('id', False):
                query.filter(id__eq=self.request.GET['id'])
            elif self.request.GET.get('country_id', False):
                query.filter(country_id__eq=self.request.GET['country_id'])

            sphinx_results = query.process()
            ...

        :param with_meta: make the `SHOW META` subquery to extract some useful meta-information (default is True).
        :param with_status: make the `SHOW STATUS` subquery to extract performance counters (default is False).

        Returns search results as dictionary with :attr:`result`, :attr:`meta` and :attr:`status` keys.
        :attr:`result` is actually some search result, a list of dictionaries with documents ids and another attributes;
        :attr:`meta` is a dictionary with some `additional meta-information
        <http://sphinxsearch.com/docs/current.html#sphinxql-show-meta>`_ about your query;
        :attr:`status` is a dictionary with `a number of useful performance counters
        <http://sphinxsearch.com/docs/current.html#sphinxql-show-status>`_.
        """
        return self._get_result(
            sxql_query=self._ql(),
            with_meta=with_meta,
            with_status=with_status,
        )


class SphinxSnippets(DBOperations):
    """
    Implements SphinxQL `CALL SNIPPETS syntax <http://sphinxsearch.com/docs/current.html#sphinxql-call-snippets>`_
    and supports full set of `excerpts parameters <http://sphinxsearch.com/docs/current.html#api-func-buildexcerpts>`_.
    Sphinx doesn`t provide documents fetching by indexes. You have to do that yourself and pass
    documents string or strings to extract the snippets from as :attr:`data`. The usage is quite simple::

        Sphinxit = SphinxConnector()
        snippets_results = Sphinxit.Snippets('some_index', data='hello world', query='hello').process()

    .. note::
        :class:`SphinxSnippets` needs connector to refer to ``searchd``, so you can't actually process
        query without initializing :class:`SphinxConnector` first.

    :param index: Sphinx index name
    :param data: a string or a list of strings to extract snippets from
    :param query: the full-text query to build snippets for
    """

    def __init__(self, index, data, query):
        self._index = index
        self._data = data
        self._query = query
        self._options = {}

    def _ql(self):
        """
        Call this method for debugging SphinxQL query::

            sxql = Sphinxit.Snippets('index', ['only good news', 'news'], query='Good News')._ql()

        .. code-block:: sql

            CALL SNIPPETS(('only good news', 'news'), 'index', 'Good News')

        """
        return SXQLSnippets(self._index, self._data, self._query, self._options).lex

    def options(self, **kwargs):
        """
        Set snippets generating parameters with :meth:`options` like this::

            Sphinxit = SphinxConnector()
            snippets_options = {'limit': 320,
                                'before_match': '<strong>',
                                'after_match': '</strong>',
                                }
            snippets_results = Sphinxit.Snippets('some_index',
                                                 data='hello world',
                                                 query='hello').options(**snippets_options).process()

        or like this::

            Sphinxit = SphinxConnector()
            snippets_results = Sphinxit.Snippets('some_index',
                                                 data='hello world',
                                                 query='hello').options(limit=320, allow_empty=True).process()
        """
        self._options = kwargs
        return self

    def process(self):
        """
        The query is not processed until you call the :meth:`process` method.
        Returns the list of snippets or single string if it`s the only one.
        """
        results = self._get_result(self._ql(), with_meta=False, with_status=False)
        snippets = [x['snippet'] for x in results['result'] if x]

        return snippets[0] if len(snippets) == 1 else snippets
