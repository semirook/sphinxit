from __future__ import unicode_literals
from __future__ import absolute_import

from unittest import TestCase
from ..search import SphinxConnector, SphinxSearch, SphinxSnippets
from ..core.exceptions import SphinxQLSyntaxException, ImproperlyConfigured
from ..core.lexemes import Q, Avg, Count


class TestSQLConnector(TestCase):

    def test_no_connector(self):
        self.assertRaises(ImproperlyConfigured, lambda: SphinxSearch('index').process())
        self.assertRaises(ImproperlyConfigured, lambda: SphinxSnippets('index', ['data'], 'query').process())


class TestSQLProcessor(TestCase):

    def setUp(self):
        self.SphinxSearch = SphinxConnector().Search

    def test_instance(self):
        self.assertTrue(isinstance(self.SphinxSearch('index'), SphinxSearch))

    def test_basic_query(self):
        self.assertEqual(self.SphinxSearch('index')._ql(),
                         'SELECT * FROM index')
        self.assertEqual(self.SphinxSearch('index', 'index_delta')._ql(),
                         'SELECT * FROM index, index_delta')
        self.assertRaises(SphinxQLSyntaxException, self.SphinxSearch)

    def test_select(self):
        self.assertEqual(self.SphinxSearch('index').select('id')._ql(),
                         'SELECT id FROM index')
        self.assertEqual(self.SphinxSearch('index').select('id').select('title')._ql(),
                         'SELECT id, title FROM index')
        self.assertEqual(self.SphinxSearch('index').select(Avg('price')).select('title')._ql(),
                         'SELECT title, AVG(price) AS price_avg FROM index')

    def test_order_by(self):
        self.assertEqual(self.SphinxSearch('index').order_by('title', 'asc')._ql(),
                         'SELECT * FROM index ORDER BY title ASC')
        self.assertEqual(self.SphinxSearch('index').order_by('title', 'asc').order_by('name', 'desc')._ql(),
                         'SELECT * FROM index ORDER BY title ASC, name DESC')

    def test_limit(self):
        self.assertEqual(self.SphinxSearch('index').limit(0, 20)._ql(),
                         'SELECT * FROM index LIMIT 0,20')
        self.assertRaises(SphinxQLSyntaxException,
                          lambda: self.SphinxSearch('index').limit(0, 200).limit(10, 60)._ql())

    def test_group_by(self):
        self.assertEqual(self.SphinxSearch('index').group_by('title')._ql(),
                         'SELECT * FROM index GROUP BY title')
        self.assertEqual(self.SphinxSearch('index').group_by()._ql(),
                         'SELECT * FROM index')
        self.assertRaises(SphinxQLSyntaxException,
                          lambda: self.SphinxSearch('index').group_by('title').group_by('name')._ql())

    def test_cluster(self):
        self.assertEqual(self.SphinxSearch('index').cluster('title')._ql(),
                         'SELECT *, COUNT(*) AS num FROM index GROUP BY title')
        self.assertEqual(self.SphinxSearch('index').select(Count()).group_by('title')._ql(),
                         'SELECT *, COUNT(*) AS num FROM index GROUP BY title')
        self.assertEqual(self.SphinxSearch('index').cluster('title', alias='same_titles')._ql(),
                         'SELECT *, COUNT(*) AS same_titles FROM index GROUP BY title')
        self.assertEqual(self.SphinxSearch('index').cluster()._ql(),
                         'SELECT * FROM index')
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: self.SphinxSearch('index').cluster('title').cluster('name')._ql(),
        )

    def test_within_group_order_by(self):
        self.assertEqual(self.SphinxSearch('index').within_group_order_by('title', 'ASC')._ql(),
                         'SELECT * FROM index WITHIN GROUP ORDER BY title ASC')
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: (self.SphinxSearch('index')
                         .within_group_order_by('title', 'ASC')
                         .within_group_order_by('name', 'DESC')._ql()))

    def test_match(self):
        self.assertEqual(self.SphinxSearch('index').match('Hello')._ql(),
                         "SELECT * FROM index WHERE MATCH('Hello')")
        self.assertEqual(self.SphinxSearch('index').match('semirook@gmail.com')._ql(),
                         r"SELECT * FROM index WHERE MATCH('semirook\\@gmail.com')")
        self.assertEqual(
            self.SphinxSearch('index').match('Hello').match('@world yeah', escape=False)._ql(),
            "SELECT * FROM index WHERE MATCH('Hello @world yeah')",
        )

    def test_filters(self):
        self.assertEqual(self.SphinxSearch('index').filter(id__gte=1)._ql(),
                         "SELECT * FROM index WHERE id>=1")
        self.assertEqual(self.SphinxSearch('index').filter(id__gte=1, counter__in=[1, 5])._ql(),
                         "SELECT * FROM index WHERE id>=1 AND counter IN (1,5)")
        self.assertEqual(self.SphinxSearch('index').filter(id__gte=1).filter(counter__in=[1, 5])._ql(),
                         "SELECT * FROM index WHERE id>=1 AND counter IN (1,5)")
        self.assertIn(
            self.SphinxSearch('index').filter(Q(id__eq=1, id__gte=5))._ql(),
            ("SELECT *, (id>=5 AND id=1) AS cnd FROM index WHERE cnd>0",
             "SELECT *, (id=1 AND id>=5) AS cnd FROM index WHERE cnd>0"),
        )
        self.assertIn(
            (self.SphinxSearch('index').filter(Q(id__eq=1) | Q(id__gte=5))
                                       .filter(Q(counter__lt=42, id__lt=20))
                                       .filter(id__eq=2)
                                       ._ql()),
            ["SELECT *, {or_q} AS cnd FROM index WHERE cnd>0 AND id=2".format(or_q=or_q)
             for or_q in ("(id=1) OR (id>=5) AND (counter<42 AND id<20)", "(id=1) OR (id>=5) AND (id<20, counter<42)")]
        )
        self.assertIn(
            self.SphinxSearch('index').filter(~Q(id__eq=1, id__gte=5) & Q(counter__eq=1, counter__gte=100))._ql(),
            ["SELECT *, {or_q} AS cnd FROM index WHERE cnd>0".format(or_q=or_q)
             for or_q in ("(id=1 OR id>=5) AND (counter=1 AND counter>=100)",
                          "(id=1 OR id>=5) AND (counter>=100 AND counter=1)",
                          "(id>=5 OR id=1) AND (counter=1 AND counter>=100)",
                          "(id>=5 OR id=1) AND (counter>=100 AND counter=1)")]
        )
        self.assertIn(
            (self.SphinxSearch('index').filter(institute__eq=6506)
                                       .filter(location__eq=1565)
                                       .cluster('location')
                                       .filter(Q(id__eq=1, id__gte=5))
                                       ._ql()),
            ["SELECT *, COUNT(*) AS num, {or_q} AS cnd FROM index WHERE institute=6506 AND location=1565 AND cnd>0 GROUP BY location"
            .format(or_q=or_q) for or_q in ("(id>=5 AND id=1)", "(id=1 AND id>=5)")]
        )

    def test_match_with_filters(self):
        self.assertEqual(self.SphinxSearch('index').match('Hello').filter(id__gte=1)._ql(),
                         "SELECT * FROM index WHERE MATCH('Hello') AND id>=1")

    def test_select_with_filters(self):
        self.assertEqual(
            self.SphinxSearch('index').select('id').match('Hello').filter(Q(id__eq=1) | Q(id__gte=5))._ql(),
            "SELECT id, (id=1) OR (id>=5) AS cnd FROM index WHERE MATCH('Hello') AND cnd>0",
        )


class TestSnippets(TestCase):

    def setUp(self):
        self.SphinxSnippets = SphinxConnector().Snippets

    def test_instance(self):
        self.assertIsInstance(self.SphinxSnippets('index', ['only good news'], query='Good News'), SphinxSnippets)

    def test_basic(self):
        self.assertEqual(
            self.SphinxSnippets('index', ['only good news', 'news'], query='Good News')._ql(),
            "CALL SNIPPETS(('only good news', 'news'), 'index', 'Good News')",
        )
        self.assertEqual(
            self.SphinxSnippets('index', 'only good news', query='Good News')._ql(),
            "CALL SNIPPETS(('only good news'), 'index', 'Good News')",
        )

    def test_options(self):
        query = self.SphinxSnippets('index', ['only good news', 'news'], 'Good News').options(**{'limit': 320})
        self.assertEqual(query._ql(), "CALL SNIPPETS(('only good news', 'news'), 'index', 'Good News', 320 AS limit)")
