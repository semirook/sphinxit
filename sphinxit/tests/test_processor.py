# -*- coding: utf-8 -*-
from unittest import TestCase
from mock import patch, Mock
from ..search import SphinxConnector, SphinxSearch, SphinxSnippets
from ..core.exceptions import SphinxQLSyntaxException, ImproperlyConfigured
from ..core.lexemes import Q, Avg, Count


class TestSQLConnector(TestCase):

    def test_no_connector(self):
        self.assertRaises(ImproperlyConfigured, lambda: SphinxSearch('index').process())
        self.assertRaises(ImproperlyConfigured, lambda: SphinxSnippets('index', ['data'], 'query').process())


class TestSQLProcessor(TestCase):

    def setUp(self):
        self.SphinxSearch = SphinxConnector()

    def test_instance(self):
        self.assertTrue(isinstance(self.SphinxSearch('index'), SphinxSearch))
        self.assertTrue(isinstance(self.SphinxSearch.Index('index'), SphinxSearch))

    def test_basic_query(self):
        a = self.SphinxSearch('index').get_sxql()
        self.assertEqual(a, u'SELECT * FROM index')

        b = self.SphinxSearch('index', 'index_delta').get_sxql()
        self.assertEqual(b, u'SELECT * FROM index, index_delta')

        self.assertRaises(SphinxQLSyntaxException, self.SphinxSearch)

    def test_select(self):
        a = self.SphinxSearch('index').select('id').get_sxql()
        self.assertEqual(a, u'SELECT id FROM index')

        b = self.SphinxSearch('index').select('id').select('title').get_sxql()
        self.assertEqual(b, u'SELECT id, title FROM index')

        c = self.SphinxSearch('index').select(Avg('price')).select('title').get_sxql()
        self.assertEqual(c, u'SELECT title, AVG(price) AS price_avg FROM index')

    def test_order_by(self):
        a = self.SphinxSearch('index').order_by('title', 'asc').get_sxql()
        self.assertEqual(a, u'SELECT * FROM index ORDER BY title ASC')

        b = self.SphinxSearch('index').order_by('title', 'asc').order_by('name', 'desc').get_sxql()
        self.assertEqual(b, u'SELECT * FROM index ORDER BY title ASC, name DESC')

    def test_limit(self):
        a = self.SphinxSearch('index').limit(0, 20).get_sxql()
        self.assertEqual(a, u'SELECT * FROM index LIMIT 0,20')

        self.assertRaises(SphinxQLSyntaxException, lambda: self.SphinxSearch('index').limit(0, 200).limit(10, 60).get_sxql())

    def test_group_by(self):
        a = self.SphinxSearch('index').group_by('title').get_sxql()
        self.assertEqual(a, u'SELECT * FROM index GROUP BY title')

        b = self.SphinxSearch('index').group_by().get_sxql()
        self.assertEqual(b, u'SELECT * FROM index')

        self.assertRaises(SphinxQLSyntaxException, lambda: self.SphinxSearch('index').group_by('title').group_by('name').get_sxql())

    def test_cluster(self):
        a = self.SphinxSearch('index').cluster('title').get_sxql()
        self.assertEqual(a, u'SELECT *, COUNT(*) AS num FROM index GROUP BY title')

        b = self.SphinxSearch('index').cluster('title', alias='same_titles').get_sxql()
        self.assertEqual(b, u'SELECT *, COUNT(*) AS same_titles FROM index GROUP BY title')

        c = self.SphinxSearch('index').cluster().get_sxql()
        self.assertEqual(c, u'SELECT * FROM index')

        d = self.SphinxSearch('index').select(Count()).group_by('title').get_sxql()
        self.assertEqual(a, d)

        self.assertRaises(SphinxQLSyntaxException, lambda: self.SphinxSearch('index').cluster('title').cluster('name').get_sxql())

    def test_within_group_order_by(self):
        a = self.SphinxSearch('index').within_group_order_by('title', 'ASC').get_sxql()
        self.assertEqual(a, u'SELECT * FROM index WITHIN GROUP ORDER BY title ASC')

        self.assertRaises(SphinxQLSyntaxException, lambda: self.SphinxSearch('index').within_group_order_by('title', 'ASC').within_group_order_by('name', 'DESC').get_sxql())

    def test_match(self):
        a = self.SphinxSearch('index').match('Hello').get_sxql()
        self.assertEqual(a, "SELECT * FROM index WHERE MATCH('Hello')")

        b = self.SphinxSearch('index').match('Hello').match('@world yeah', escape=False).get_sxql()
        self.assertEqual(b, "SELECT * FROM index WHERE MATCH('Hello @world yeah')")

        c = self.SphinxSearch('index').match('semirook@gmail.com').get_sxql()
        self.assertEqual(c, r"SELECT * FROM index WHERE MATCH('semirook\\@gmail.com')")

    def test_filters(self):
        a = self.SphinxSearch('index').filter(id__gte=1).get_sxql()
        self.assertEqual(a, "SELECT * FROM index WHERE id>=1")

        b = self.SphinxSearch('index').filter(id__gte=1, counter__in=[1, 5]).get_sxql()
        self.assertEqual(b, "SELECT * FROM index WHERE id>=1 AND counter IN (1,5)")

        c = self.SphinxSearch('index').filter(id__gte=1).filter(counter__in=[1, 5]).get_sxql()
        self.assertEqual(c, "SELECT * FROM index WHERE id>=1 AND counter IN (1,5)")

        d = self.SphinxSearch('index').filter(Q(id__eq=1, id__gte=5)).get_sxql()
        d_results = ["SELECT *, (id>=5 AND id=1) AS cnd FROM index WHERE cnd>0",
                     "SELECT *, (id=1 AND id>=5) AS cnd FROM index WHERE cnd>0"]
        self.assertTrue(d in d_results)

        e = (self.SphinxSearch('index').filter(Q(id__eq=1) | Q(id__gte=5))
                                       .filter(Q(counter__lt=42, id__lt=20))
                                       .filter(id__eq=2)
                                       .get_sxql())
        e_possible_q_orders = ["(id=1) OR (id>=5) AND (counter<42 AND id<20)",
                               "(id=1) OR (id>=5) AND (id<20, counter<42)"]
        e_possible_queries = ["SELECT *, {or_q} AS cnd FROM index WHERE cnd>0 AND id=2".format(or_q=or_q) for or_q in e_possible_q_orders]
        self.assertTrue(e in e_possible_queries)

        f = self.SphinxSearch('index').filter(~Q(id__eq=1, id__gte=5) & Q(counter__eq=1, counter__gte=100)).get_sxql()
        f_possible_q_orders = ["(id=1 OR id>=5) AND (counter=1 AND counter>=100)",
                               "(id=1 OR id>=5) AND (counter>=100 AND counter=1)",
                               "(id>=5 OR id=1) AND (counter=1 AND counter>=100)",
                               "(id>=5 OR id=1) AND (counter>=100 AND counter=1)"]
        f_possible_queries = ["SELECT *, {or_q} AS cnd FROM index WHERE cnd>0".format(or_q=or_q) for or_q in f_possible_q_orders]
        self.assertTrue(f in f_possible_queries)

        g = (self.SphinxSearch('index').filter(institute__eq=6506)
                                       .filter(location__eq=1565)
                                       .cluster('location')
                                       .filter(Q(id__eq=1, id__gte=5))
                                       .get_sxql())
        g_possible_q_orders = ["(id>=5 AND id=1)", "(id=1 AND id>=5)"]
        g_possible_queries = ["SELECT *, COUNT(*) AS num, {or_q} AS cnd FROM index WHERE institute=6506 AND location=1565 AND cnd>0 GROUP BY location"
                              .format(or_q=or_q) for or_q in g_possible_q_orders]
        self.assertTrue(g in g_possible_queries)

    def test_match_with_filters(self):
        a = self.SphinxSearch('index').match('Hello').filter(id__gte=1).get_sxql()
        self.assertEqual(a, "SELECT * FROM index WHERE MATCH('Hello') AND id>=1")

    def test_select_with_filters(self):
        a = self.SphinxSearch('index').select('id').match('Hello').filter(Q(id__eq=1) | Q(id__gte=5)).get_sxql()
        self.assertEqual(a, "SELECT id, (id=1) OR (id>=5) AS cnd FROM index WHERE MATCH('Hello') AND cnd>0")


class TestSnippets(TestCase):

    def setUp(self):
        self.SphinxSearch = SphinxConnector()

    def test_instance(self):
        self.assertTrue(isinstance(self.SphinxSearch.Snippets('index', ['only good news'], query='Good News'), SphinxSnippets))

    def test_basic(self):
        query_1 = self.SphinxSearch.Snippets('index', ['only good news', 'news'], query='Good News').get_sxql()
        self.assertEqual(query_1, "CALL SNIPPETS(('only good news', 'news'), 'index', 'Good News')")

        query_2 = self.SphinxSearch.Snippets('index', 'only good news', query='Good News').get_sxql()
        self.assertEqual(query_2, "CALL SNIPPETS(('only good news'), 'index', 'Good News')")

    def test_options(self):
        query = self.SphinxSearch.Snippets('index', ['only good news', 'news'], 'Good News').options(**{'limit': 320})
        self.assertEqual(query.get_sxql(), u"CALL SNIPPETS(('only good news', 'news'), 'index', 'Good News', 320 AS limit)")
