# -*- coding: utf-8 -*-
from unittest import TestCase
from ..core.lexemes import (SXQLSelect, SXQLFrom, SXQLLimit, SXQLOrder,
                            SXQLGroupBy, SXQLWithinGroupOrderBy,
                            SXQLMatch, SXQLFilter, SXQLORFilter,
                            Q, Count, Avg, Min, Max, Sum, SXQLSnippets)
from ..core.exceptions import SphinxQLSyntaxException


class TestSXQLSelect(TestCase):

    def test_initial(self):
        sxql_inst = SXQLSelect()
        self.assertEqual(sxql_inst.lex, u'SELECT *')

        sxql_inst('title', 'name')
        self.assertEqual(sxql_inst.lex, u'SELECT title, name')

    def test_duplicate_args(self):
        sxql_inst = SXQLSelect()
        sxql_inst('title', 'title', 'name')
        self.assertEqual(sxql_inst.lex, u'SELECT title, name')

    def test_wrong_args(self):
        sxql_inst_1 = SXQLSelect()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_1, 42)

        sxql_inst_2 = SXQLSelect()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_2, ['title', 'name'])


class TestSXQLFrom(TestCase):

    def test_initial(self):
        sxql_inst = SXQLFrom()
        sxql_inst('index')
        self.assertEqual(sxql_inst.lex, u'FROM index')

        sxql_inst('delta_index')
        self.assertEqual(sxql_inst.lex, u'FROM index, delta_index')

    def test_duplicate_args(self):
        sxql_inst = SXQLFrom()
        sxql_inst('index', 'index', 'delta_index')
        self.assertEqual(sxql_inst.lex, u'FROM index, delta_index')

    def test_wrong_args(self):
        sxql_inst_1 = SXQLFrom()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_1)

        sxql_inst_2 = SXQLFrom()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_2, ['index'])


class TestSXQLLimit(TestCase):

    def test_initial(self):
        sxql_inst = SXQLLimit()
        self.assertEqual(sxql_inst.lex, u'LIMIT 0,1000')

        sxql_inst(10, 20)
        self.assertEqual(sxql_inst.lex, u'LIMIT 10,20')

    def test_unique_call(self):
        sxql_inst = SXQLLimit()
        sxql_inst(10, 20)
        self.assertRaises(SphinxQLSyntaxException, sxql_inst, (100, 500))

    def test_wrong_attrs(self):
        sxql_inst_1 = SXQLLimit()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_1, 10)

        sxql_inst_2 = SXQLLimit()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_2, 10, 14, 14)

        sxql_inst_2 = SXQLLimit()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_2, '10', '20')

        sxql_inst_3 = SXQLLimit()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_3)


class TestSXQLOrder(TestCase):

    def test_initial(self):
        sxql_inst = SXQLOrder()
        sxql_inst('title', 'ASC')
        self.assertEqual(sxql_inst.lex, u'ORDER BY title ASC')

        sxql_inst('name', 'desc')
        self.assertEqual(sxql_inst.lex, u'ORDER BY title ASC, name DESC')

    def test_wrong_attrs(self):
        sxql_inst_1 = SXQLOrder()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_1, 'name')

        sxql_inst_2 = SXQLOrder()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_2, 42, 'DESC')

        sxql_inst_3 = SXQLOrder()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_3)

        sxql_inst_4 = SXQLOrder()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_4, 'name', 'REST')


class TestSXQLGroupBy(TestCase):

    def test_initial(self):
        sxql_inst = SXQLGroupBy()
        sxql_inst('name')
        self.assertEqual(sxql_inst.lex, u'GROUP BY name')

    def test_wrong_attrs(self):
        sxql_inst_1 = SXQLGroupBy()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_1, 42)

        sxql_inst_2 = SXQLGroupBy()
        sxql_inst_2('title')
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_2, 'name')

        sxql_inst_3 = SXQLGroupBy()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_3, 'name', 'title')


class TestSXQLWithinGroupOrderBy(TestCase):

    def test_initial(self):
        sxql_inst = SXQLWithinGroupOrderBy()
        sxql_inst('name', 'asc')
        self.assertEqual(sxql_inst.lex, u'WITHIN GROUP ORDER BY name ASC')

    def test_unique_call(self):
        sxql_inst = SXQLWithinGroupOrderBy()
        sxql_inst('name', 'asc')
        self.assertRaises(SphinxQLSyntaxException, sxql_inst, 'title', 'desc')

    def test_wrong_attrs(self):
        sxql_inst_1 = SXQLWithinGroupOrderBy()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst_1, 'name')


class TestSXQLFilter(TestCase):

    def test_initial(self):
        where_def_1 = SXQLFilter()(id__eq=1)
        self.assertEqual(where_def_1.lex, u'id=1')

        where_def_2 = SXQLFilter()(id__gt=1)
        self.assertEqual(where_def_2.lex, u'id>1')

        where_def_3 = SXQLFilter()(id__gte=1)
        self.assertEqual(where_def_3.lex, u'id>=1')

        where_def_4 = SXQLFilter()(id__lt=1)
        self.assertEqual(where_def_4.lex, u'id<1')

        where_def_5 = SXQLFilter()(id__lte=1)
        self.assertEqual(where_def_5.lex, u'id<=1')

        where_def_6 = SXQLFilter()(id__in=[1, 2])
        self.assertEqual(where_def_6.lex, u'id IN (1,2)')

        where_def_7 = SXQLFilter()(id__between=[1, 5])
        self.assertEqual(where_def_7.lex, u'id BETWEEN 1 AND 5')

        where_def_8 = SXQLFilter()(e__eq=15)
        self.assertEqual(where_def_8.lex, u'e=15')

        where_def_9 = SXQLFilter()(id__in=['2', '4', 5])
        self.assertEqual(where_def_9.lex, u'id IN (2,4,5)')

        more_where_defs = SXQLFilter()(id__eq=1, att1__lt=1, att2__between=[1, 5])
        results = ('id=1 AND att2 BETWEEN 1 AND 5 AND att1<1',
                   'id=1 AND att1<1 AND att2 BETWEEN 1 AND 5',
                   'att2 BETWEEN 1 AND 5 AND att1<1 AND id=1',
                   'att2 BETWEEN 1 AND 5 AND id=1 AND att1<1',
                   'att1<1 AND id=1 AND att2 BETWEEN 1 AND 5',
                   'att1<1 AND att2 BETWEEN 1 AND 5 AND id=1',
                   )
        self.assertTrue(more_where_defs.lex in results)

    def test_wrong_attrs(self):
        where_def_1 = SXQLFilter()
        self.assertRaises(SphinxQLSyntaxException, where_def_1, id__e=1)

        where_def_2 = SXQLFilter()
        self.assertRaises(SphinxQLSyntaxException, where_def_2, id__gte=(16, 32))

        where_def_3 = SXQLFilter()
        self.assertRaises(SphinxQLSyntaxException, where_def_3, title__eq='Error')


class TestSXQLMatch(TestCase):

    def test_initial(self):
        sxql_inst = SXQLMatch()
        sxql_inst('Find me some money')
        self.assertEqual(sxql_inst.lex, u"MATCH('Find me some money')")

    def test_match_join_and_escape(self):
        sxql_inst = SXQLMatch()
        sxql_inst('@full_name ^Roman')
        sxql_inst('@full_name Semirook$')
        self.assertEqual(sxql_inst.lex, ur"MATCH('\\@full_name \\^Roman \\@full_name Semirook\\$')")

    def test_quotes_escape(self):
        sxql_inst = SXQLMatch()
        sxql_inst('"name')
        self.assertEqual(sxql_inst.lex, ur"MATCH('{0}')".format(r'\\"name'))

        sxql_inst_2 = SXQLMatch()
        sxql_inst_2("l'amour")
        self.assertEqual(sxql_inst_2.lex, ur"MATCH('lamour')")

    def test_unescaped_query(self):
        sxql_inst = SXQLMatch()
        mail_query = '@email "semirook@gmail.com"'
        sxql_inst(mail_query, escape=False)
        self.assertEqual(sxql_inst.lex, u"MATCH('{0}')".format(mail_query))

    def test_wrong_query(self):
        sxql_inst = SXQLMatch()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst, 42)


class TestQ(TestCase):

    def test_initial(self):
        sxql_inst = Q(id__eq=1)
        self.assertEqual(sxql_inst.lex, "(id=1)")

    def test_concat(self):
        sxql_inst = Q(id__eq=1, id__gte=5)
        results = ['(id=1 AND id>=5)', '(id>=5 AND id=1)']
        self.assertTrue(sxql_inst.lex in results)

    def test_negative_concat(self):
        sxql_inst = ~Q(id__eq=1, id__gte=5)
        results = ['(id=1 OR id>=5)', '(id>=5 OR id=1)']
        self.assertTrue(sxql_inst.lex in results)


class TestSXQLORFilter(TestCase):

    def test_basics(self):
        sxql_inst_1 = SXQLORFilter()(Q(id__eq=1) | Q(id__gte=5))
        self.assertEqual(sxql_inst_1.lex, u'(id=1) OR (id>=5) AS cnd')

        sxql_inst_2 = SXQLORFilter()(Q(id__eq=1) & Q(id__gte=5))
        self.assertEqual(sxql_inst_2.lex, u'(id=1) AND (id>=5) AS cnd')

        sxql_inst_3 = SXQLORFilter()(Q(id__eq=1) & Q(id__gte=5) | Q(counter__between=[1, 5]))
        self.assertEqual(sxql_inst_3.lex, u'(id=1) AND (id>=5) OR (counter BETWEEN 1 AND 5) AS cnd')

        sxql_inst_4 = SXQLORFilter()(Q(id__eq=1) & (Q(id__gte=5) | Q(id__lt=4)))
        self.assertEqual(sxql_inst_4.lex, u'(id>=5) OR (id<4) AND (id=1) AS cnd')

    def test_complex_expression(self):
        sxql_inst_1 = SXQLORFilter()(Q(id__eq=1, id__gte=5) | ~Q(counter__in=[1, 5], id__eq=42))
        results = ['(id>=5 AND id=1) OR (counter IN (1,5) OR id=42) AS cnd',
                   '(id=1 AND id>=5) OR (counter IN (1,5) OR id=42) AS cnd',
                   '(id>=5 AND id=1) OR (id=42 OR counter IN (1,5)) AS cnd',
                   '(id=1 AND id>=5) OR (id=42 OR counter IN (1,5)) AS cnd']
        self.assertTrue(sxql_inst_1.lex in results)

    def test_wrong_attrs(self):
        sxql_inst_1 = SXQLORFilter()(Q(id__eq=1) + Q(id__gte=5))
        self.assertEqual(sxql_inst_1.lex, u'(id=1) AND (id>=5) AS cnd')


class TestCount(TestCase):

    def test_basics(self):
        sxql_inst_1 = Count()
        self.assertEqual(sxql_inst_1.lex, u'COUNT(*) AS num')

        sxql_inst_2 = Count('counter')
        self.assertEqual(sxql_inst_2.lex, u'COUNT(DISTINCT counter) AS counter_count')

        sxql_inst_3 = Count('counter', 'my_alias')
        self.assertEqual(sxql_inst_3.lex, u'COUNT(DISTINCT counter) AS my_alias')

        sxql_inst_4 = Count(alias='my_alias')
        self.assertEqual(sxql_inst_4.lex, u'COUNT(*) AS my_alias')

    def test_wrong_attr(self):
        with self.assertRaises(SphinxQLSyntaxException):
            Count(['counter']).lex

        with self.assertRaises(SphinxQLSyntaxException):
            Count(alias='count').lex


class TestAvg(TestCase):

    def test_basics(self):
        sxql_inst_1 = Avg('price')
        self.assertEqual(sxql_inst_1.lex, u'AVG(price) AS price_avg')

        sxql_inst_2 = Avg('price', 'price_mid')
        self.assertEqual(sxql_inst_2.lex, u'AVG(price) AS price_mid')

    def test_wrong_attr(self):
        with self.assertRaises(SphinxQLSyntaxException):
            Avg(['counter']).lex

        with self.assertRaises(SphinxQLSyntaxException):
            Avg('counter', 154).lex


class TestMin(TestCase):

    def test_basics(self):
        sxql_inst_1 = Min('price')
        self.assertEqual(sxql_inst_1.lex, u'MIN(price) AS price_min')

        sxql_inst_2 = Min('price', 'minimal')
        self.assertEqual(sxql_inst_2.lex, u'MIN(price) AS minimal')

    def test_wrong_attr(self):
        with self.assertRaises(SphinxQLSyntaxException):
            Min(['price']).lex

        with self.assertRaises(SphinxQLSyntaxException):
            Min('price', 154).lex


class TestMax(TestCase):

    def test_basics(self):
        sxql_inst_1 = Max('price')
        self.assertEqual(sxql_inst_1.lex, u'MAX(price) AS price_max')

        sxql_inst_2 = Max('price', 'maximum')
        self.assertEqual(sxql_inst_2.lex, u'MAX(price) AS maximum')

    def test_wrong_attr(self):
        with self.assertRaises(SphinxQLSyntaxException):
            Max(['price']).lex

        with self.assertRaises(SphinxQLSyntaxException):
            Max('price', 154).lex


class TestSum(TestCase):

    def test_basics(self):
        sxql_inst_1 = Sum('counter')
        self.assertEqual(sxql_inst_1.lex, u'SUM(counter) AS counter_sum')

        sxql_inst_2 = Sum('counter', 'summary')
        self.assertEqual(sxql_inst_2.lex, u'SUM(counter) AS summary')

    def test_wrong_attr(self):
        with self.assertRaises(SphinxQLSyntaxException):
            Sum(['counter']).lex

        with self.assertRaises(SphinxQLSyntaxException):
            Sum('counter', 154).lex


class TestSXQLSnippets(TestCase):

    def test_basics(self):
        sxql_inst_1 = SXQLSnippets('index', data=['only good news'], query='Good News')
        self.assertEqual(sxql_inst_1.lex, "CALL SNIPPETS(('only good news'), 'index', 'Good News')")

    def test_with_options_1(self):
        snippet_options = {'limit': 320,
                           'allow_empty': True,
                           }
        possible_options_ordering = ["320 AS limit, 1 AS allow_empty", "1 AS allow_empty, 320 AS limit"]
        sxql_inst = SXQLSnippets('index', data=['only good news'], query='Good News', options=snippet_options)
        possible_queries = ["CALL SNIPPETS(('only good news'), 'index', 'Good News', {opts})".format(opts=opts) for opts in possible_options_ordering]
        self.assertIn(sxql_inst.lex, possible_queries)

    def test_with_options_2(self):
        snippet_options = {'before_match': '<strong>',
                           'after_match': '</strong>',
                           }
        possible_options_ordering = ["'<strong>' AS before_match, '</strong>' AS after_match",
                                     "'</strong>' AS after_match, '<strong>' AS before_match"]
        sxql_inst = SXQLSnippets('index', data=['only good news'], query='Good News', options=snippet_options)
        possible_queries = ["CALL SNIPPETS(('only good news'), 'index', 'Good News', {opts})".format(opts=opts) for opts in possible_options_ordering]
        self.assertIn(sxql_inst.lex, possible_queries)

    def test_wrong_usage(self):
        with self.assertRaises(SphinxQLSyntaxException):
            SXQLSnippets(['good news and bad news', 'only good news'], 'index', 'Good News').lex

        with self.assertRaises(SphinxQLSyntaxException):
            SXQLSnippets('index', 'Good News', ['good news and bad news', 'only good news']).lex

        with self.assertRaises(SphinxQLSyntaxException):
            SXQLSnippets('index', 'Good News', {}, ['good news and bad news', 'only good news']).lex

    def test_wrong_options_param(self):
        wrong_param_snippet_options = {'before_match': '<strong>',
                                       'aftermatch': '</strong>',
                                       }
        with self.assertRaises(SphinxQLSyntaxException):
            SXQLSnippets('index', data=['only good news'], query='Good News', options=wrong_param_snippet_options).lex

        wrong_value_snippet_options = {'allow_empty': 12}
        with self.assertRaises(SphinxQLSyntaxException):
            SXQLSnippets('index', data=['only good news'], query='Good News', options=wrong_value_snippet_options).lex

        wrong_value_snippet_options = {'html_strip_mode': 'wrong_mode'}
        with self.assertRaises(SphinxQLSyntaxException):
            SXQLSnippets('index', data=['only good news'], query='Good News', options=wrong_value_snippet_options).lex

    def test_quotes_escaping(self):
        sxql_inst_1 = SXQLSnippets('index', data=["only l'amour", "l'oreal"], query="L'amour")
        self.assertEqual(sxql_inst_1.lex, u"CALL SNIPPETS(('only lamour', 'loreal'), 'index', 'Lamour')")
