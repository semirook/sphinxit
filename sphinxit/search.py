# -*- coding: utf-8 -*-

"""
    sphinxit.search
    ~~~~~~~~~~~~~~~

    Implements Sphinxit facade classes.

    :copyright: 2012 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

try:
    import MySQLdb as mysql
except ImportError:
    mysql = None

from core.exceptions import SphinxQLDriverException, SphinxQLSyntaxException, ImproperlyConfigured
from core.processor import SphinxSearchBase
from core.lexemes import SXQLSnippets


class DBOperations(object):
    """Common set of methods for fetching index data by raw SphinxQL query"""

    @property
    def connection(self):
        raise NotImplementedError

    def _get_data(self, sql_query):
        if mysql is None:
            raise ImproperlyConfigured('I need MySQLdb.')

        try:
            self.connection.query(sql_query.encode('utf-8'))
        except NotImplementedError:
            raise SphinxQLDriverException('Specify proper SphinxQL connection.')
        except mysql.DatabaseError:
            raise SphinxQLSyntaxException(u'Cannot process query: {0}.'.format(sql_query))

        result = self.connection.store_result()

        return result.fetch_row(maxrows=0, how=1)

    def _get_meta_info(self):
        sxql_query = "SHOW META"
        result = self._get_data(sxql_query)
        info = dict([(x['Variable_name'], x['Value']) for x in result])

        return info


class SphinxConnector(object):
    """
    The start point of your new Sphinx-based search.
    Connects to the ``searchd`` via MySQL interface and this is how SphinxQL actually works,
    it speaks the same language as the MySQL network protocol. So make sure you have
    ``MySQLdb`` package installed.

    :param host: ``searchd`` host IP address
    :param port: ``searchd`` port specified in your `sphinx.conf`

    Default host for every new connection is `127.0.0.1` and it's suitable in most cases.
    Default port is `9306`, compare it with specified one in your `sphinx.conf`::

        searchd {
            listen = 9306:mysql41
        }

    For example, standard usage is::

        Sphinxit = SphinxConnector()
        search_results = Sphinxit('some_index').match('Hello!').process()

    You can have multiple connections to the ``searchd`` with different configurations
    via different ports if you whant to::

        StandardSphinxit = SphinxConnector()
        some_results = StandardSphinxit('some_index').match('Hello!').process()

        SpecificSphinxit = SphinxConnector(port=9350)
        another_results = SpecificSphinxit('some_index').match('Hello!').process()

    :raises SphinxQLDriverException: if can't connect to the ``searchd`` for some reasons.
    :raises ImproperlyConfigured: if ``MySQLdb`` package is not installed.

    `SphinxConnector` provides simple instance constructors for :class:`SphinxSearch` and :class:`SphinxSnippets`
    and attaches proper :attr:`connection` to them::

        Sphinxit = SphinxConnector()
        search_results = Sphinxit.Index('some_index').match('Hello!').process()
        snippets_results = Sphinxit.Snippets('some_index', data='hello world', query='hello').process()
    """

    def __init__(self, **kwargs):
        default_connection = {'host': '127.0.0.1', 'port': 9306}
        self.host = kwargs.get('host', default_connection['host'])
        self.port = kwargs.get('port', default_connection['port'])
        self.connection = self.connect()

        if not self.host or not self.port:
            raise SphinxQLDriverException('Cannot connect to Sphinx without proper connection.')

    def __del__(self):
        self.close()

    def __call__(self, *args):
        return self.Index(*args)

    def connect(self):
        """
        There is no necessity to connect manually but in some rare cases you may need to.
        For example::

            Sphinxit = SphinxConnector()
            Sphinxit.close()
            Sphinxit.port = 9350
            Sphinxit.connect()
        """
        if mysql is None:
            raise ImproperlyConfigured('I need MySQLdb.')

        try:
            connection = mysql.connect(host=self.host, port=self.port, use_unicode=True, charset='utf8')
        except mysql.DatabaseError:
            raise SphinxQLDriverException('Cannot connect to Sphinx via SphinxQL connection.')

        return connection

    def close(self):
        """
        Closes SphinxQL connection. There is no necessity to do it manually.
        For example::

            Sphinxit = SphinxConnector()
            Sphinxit.close()
        """
        self.connection.close()

    def Index(self, *args):
        """
        :class:`SphinxSearch` instance constructor::

            Sphinxit = SphinxConnector()
            search_results = Sphinxit.Index('index', 'delta_index').match('Hello!').process()

        :param args: Sphinx index name or several indexes, separated with comma.
        """
        new_constructor = SphinxSearch
        new_constructor.connection = self.connection

        return new_constructor(*args)

    def Snippets(self, index, data, query):
        """
        :class:`SphinxSnippets` instance constructor::

            Sphinxit = SphinxConnector()
            snippets_results = Sphinxit.Snippets('some_index', data='hello world', query='hello').process()

        :param index: Sphinx index name
        :param data: a string or a list of strings to extract snippets from
        :param query: the full-text query to build snippets for
        """
        new_constructor = SphinxSnippets
        new_constructor.connection = self.connection

        return new_constructor(index, data, query)


class SphinxSnippets(DBOperations):
    """
    Implements SphinxQL `CALL SNIPPETS syntax <http://sphinxsearch.com/docs/current.html#sphinxql-call-snippets>`_
    and supports the full set of `excerpts parameters <http://sphinxsearch.com/docs/current.html#api-func-buildexcerpts>`_.
    Sphinx doesn`t provide documents fetching by indexes out of the box. You have to do it yourself and pass
    documents string or strings to extract the snippets from as :attr:`data`. The usage is quite simple::

        Sphinxit = SphinxConnector()
        snippets_results = Sphinxit.Snippets('some_index', data='hello world', query='hello').process()

    .. note::
        :class:`SphinxSnippets` needs :attr:`connector` to refer to ``searchd``, so you can't actually process
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

    def get_sxql(self):
        """
        Call this method for debugging result SphinxQL query::

            sxql = Sphinxit.Snippets('index', ['only good news', 'news'], query='Good News').get_sxql()

        .. code-block:: sql

            CALL SNIPPETS(('only good news', 'news'), 'index', 'Good News')

        """
        return SXQLSnippets(
            self._index,
            self._data,
            self._query,
            self._options).lex

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
        Returns the list of snippets or single string if it`s the only.
        """
        result = self._get_data(self.get_sxql())
        snippets = [x['snippet'] for x in result if x]

        return snippets[0] if len(snippets) == 1 else snippets


class SphinxSearch(SphinxSearchBase, DBOperations):
    """
    Implements SphinxQL `SELECT syntax <http://sphinxsearch.com/docs/current.html#sphinxql-select>`_
    and provides simple and clean way to make full-text queries, filtering, grouping, ordering search results etc.::

        Sphinxit = SphinxConnector()
        result = Sphinxit('some_index').process()

    To make search by several indexes (you will, if you have main and delta indexes, for example), just separate
    their names with comma::

        Sphinxit= SphinxConnector()
        result = Sphinxit('main_index', 'delta_index').process()

    .. note::
        :class:`SphinxSearch` needs :attr:`connector` to refer to ``searchd``, so you can't actually process
        query without initializing :class:`SphinxConnector` first.

    :param args: Sphinx index name or several indexes, separated with comma.
    """

    def process(self):
        """
        Pay attention that query is not processed until you call the :meth:`process` method.
        You can dynamically construct as heavy queries as you want and process them only once when you need results,
        as in this simple example::

            ...
            query = Sphinxit('main_index', 'delta_index').match('Good news')

            if self.request.GET.get('id'):
                query.filter(id__eq=self.request.GET['id'])
            elif self.request.GET.get('country_id'):
                query.filter(country_id__eq=self.request.GET['country_id'])

            sphinx_result = query.process()
            ...

        Returns result dictionary with :attr:`result` and :attr:`meta` keys:
        :attr:`result` is the list of dictionaries with documents ids and another specified attributes,
        :attr:`meta` is the dictionary with some `additional meta-information <http://sphinxsearch.com/docs/2.0.3/sphinxql-show-meta.html>`_
        about your query.

        Raises :exc:`SphinxQLSyntaxException` if can't process query for some reasons.
        """
        sxql = self.get_sxql()
        return {'result': self._get_data(sxql),
                'meta': self._get_meta_info()}
