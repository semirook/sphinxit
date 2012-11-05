from __future__ import unicode_literals
from __future__ import absolute_import

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from ..core.lexemes import (SXQLSelect, SXQLFrom, SXQLLimit, SXQLOrder,
                            SXQLGroupBy, SXQLWithinGroupOrderBy,
                            SXQLMatch, SXQLFilter, SXQLORFilter,
                            Q, Count, Avg, Min, Max, Sum, SXQLSnippets)
from ..core.exceptions import SphinxQLSyntaxException


class TestSXQLSelect(unittest.TestCase):

    def test_initial(self):
        sxql_inst = SXQLSelect()
        self.assertEqual(sxql_inst.lex, 'SELECT *')

        sxql_inst('title', 'name')
        self.assertEqual(sxql_inst.lex, 'SELECT title, name')

    def test_duplicate_args(self):
        sxql_inst = SXQLSelect()
        sxql_inst('title', 'title', 'name')
        self.assertEqual(sxql_inst.lex, 'SELECT title, name')

    def test_wrong_args(self):
        self.assertRaises(SphinxQLSyntaxException, SXQLSelect(), 42)
        self.assertRaises(SphinxQLSyntaxException, SXQLSelect(), ['title', 'name'])


class TestSXQLFrom(unittest.TestCase):

    def test_initial(self):
        sxql_inst = SXQLFrom()
        sxql_inst('index')
        self.assertEqual(sxql_inst.lex, 'FROM index')

        sxql_inst('delta_index')
        self.assertEqual(sxql_inst.lex, 'FROM index, delta_index')

    def test_duplicate_args(self):
        sxql_inst = SXQLFrom()
        sxql_inst('index', 'index', 'delta_index')
        self.assertEqual(sxql_inst.lex, 'FROM index, delta_index')

    def test_wrong_args(self):
        self.assertRaises(SphinxQLSyntaxException, SXQLFrom())
        self.assertRaises(SphinxQLSyntaxException, SXQLFrom(), ['index'])


class TestSXQLLimit(unittest.TestCase):

    def test_initial(self):
        sxql_inst = SXQLLimit()
        self.assertEqual(sxql_inst.lex, 'LIMIT 0,100')

        sxql_inst(10, 20)
        self.assertEqual(sxql_inst.lex, 'LIMIT 10,20')

    def test_implicit_convert(self):
        sxql_inst = SXQLLimit()
        sxql_inst('10', 20)
        self.assertEqual(sxql_inst.lex, 'LIMIT 10,20')

    def test_unique_call(self):
        sxql_inst = SXQLLimit()
        sxql_inst(10, 20)
        self.assertRaises(SphinxQLSyntaxException, sxql_inst, (100, 500))

    def test_wrong_attrs(self):
        self.assertRaises(SphinxQLSyntaxException, SXQLLimit(), 10)
        self.assertRaises(SphinxQLSyntaxException, SXQLLimit(), 10, 14, 14)
        self.assertRaises(SphinxQLSyntaxException, SXQLLimit())


class TestSXQLOrder(unittest.TestCase):

    def test_initial(self):
        sxql_inst = SXQLOrder()
        sxql_inst('title', 'ASC')
        self.assertEqual(sxql_inst.lex, 'ORDER BY title ASC')

        sxql_inst('name', 'desc')
        self.assertEqual(sxql_inst.lex, 'ORDER BY title ASC, name DESC')

    def test_wrong_attrs(self):
        self.assertRaises(SphinxQLSyntaxException, SXQLOrder(), 'name')
        self.assertRaises(SphinxQLSyntaxException, SXQLOrder(), 42, 'DESC')
        self.assertRaises(SphinxQLSyntaxException, SXQLOrder())
        self.assertRaises(SphinxQLSyntaxException, SXQLOrder(), 'name', 'REST')


class TestSXQLGroupBy(unittest.TestCase):

    def test_initial(self):
        sxql_inst = SXQLGroupBy()
        sxql_inst('name')
        self.assertEqual(sxql_inst.lex, 'GROUP BY name')

    def test_wrong_attrs(self):
        self.assertRaises(SphinxQLSyntaxException, SXQLGroupBy(), 42)
        self.assertRaises(SphinxQLSyntaxException, SXQLGroupBy()('title'), 'name')
        self.assertRaises(SphinxQLSyntaxException, SXQLGroupBy(), 'name', 'title')


class TestSXQLWithinGroupOrderBy(unittest.TestCase):

    def test_initial(self):
        sxql_inst = SXQLWithinGroupOrderBy()
        sxql_inst('name', 'asc')
        self.assertEqual(sxql_inst.lex, 'WITHIN GROUP ORDER BY name ASC')

    def test_unique_call(self):
        sxql_inst = SXQLWithinGroupOrderBy()
        sxql_inst('name', 'asc')
        self.assertRaises(SphinxQLSyntaxException, sxql_inst, 'title', 'desc')

    def test_wrong_attrs(self):
        self.assertRaises(SphinxQLSyntaxException, SXQLWithinGroupOrderBy(), 'name')


class TestSXQLFilter(unittest.TestCase):

    def test_initial(self):
        self.assertEqual(SXQLFilter()(id__eq=1).lex, 'id=1')
        self.assertEqual(SXQLFilter()(id__gt=1).lex, 'id>1')
        self.assertEqual(SXQLFilter()(id__gte=1).lex, 'id>=1')
        self.assertEqual(SXQLFilter()(id__lt=1).lex, 'id<1')
        self.assertEqual(SXQLFilter()(id__lte=1).lex, 'id<=1')
        self.assertEqual(SXQLFilter()(id__in=[1, 2]).lex, 'id IN (1,2)')
        self.assertEqual(SXQLFilter()(id__between=[1, 5]).lex, 'id BETWEEN 1 AND 5')
        self.assertEqual(SXQLFilter()(e__eq=15).lex, 'e=15')
        self.assertEqual(SXQLFilter()(id__in=['2', '4', 5]).lex, 'id IN (2,4,5)')
        self.assertEqual(SXQLFilter()(id__neq=3).lex, 'id!=3')

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
        self.assertRaises(SphinxQLSyntaxException, SXQLFilter(), id__e=1)
        self.assertRaises(SphinxQLSyntaxException, SXQLFilter(), id__gte=(16, 32))
        self.assertRaises(SphinxQLSyntaxException, SXQLFilter(), title__eq='Error')


class TestSXQLMatch(unittest.TestCase):

    def test_initial(self):
        sxql_inst = SXQLMatch()
        sxql_inst('Find me some money')
        self.assertEqual(sxql_inst.lex, "MATCH('Find me some money')")

    def test_match_join_and_escape(self):
        sxql_inst = SXQLMatch()
        sxql_inst('@full_name ^Roman')
        sxql_inst('@full_name Semirook$')
        self.assertEqual(sxql_inst.lex, r"MATCH('\\@full_name \\^Roman \\@full_name Semirook\\$')")

    def test_quotes_escape(self):
        sxql_inst = SXQLMatch()
        sxql_inst('"name')
        self.assertEqual(sxql_inst.lex, r"MATCH('{0}')".format(r'\\"name'))

        sxql_inst_2 = SXQLMatch()
        sxql_inst_2("l'amour")
        self.assertEqual(sxql_inst_2.lex, "MATCH('l\\'amour')")

    def test_unescaped_query(self):
        sxql_inst = SXQLMatch()
        mail_query = '@email "semirook@gmail.com"'
        sxql_inst(mail_query, escape=False)
        self.assertEqual(sxql_inst.lex, "MATCH('{0}')".format(mail_query))

    def test_wrong_query(self):
        sxql_inst = SXQLMatch()
        self.assertRaises(SphinxQLSyntaxException, sxql_inst, 42)


class TestQ(unittest.TestCase):

    def test_initial(self):
        self.assertEqual(Q(id__eq=1).lex, "(id=1)")

    def test_concat(self):
        q = Q(id__eq=1, id__gte=5)
        self.assertIn(q.lex, ('(id=1 AND id>=5)', '(id>=5 AND id=1)'))

    def test_negative_concat(self):
        q = ~Q(id__eq=1, id__gte=5)
        self.assertIn(q.lex, ('(id=1 OR id>=5)', '(id>=5 OR id=1)'))


class TestSXQLORFilter(unittest.TestCase):

    def test_basics(self):
        self.assertEqual(
            SXQLORFilter()(Q(id__eq=1) | Q(id__gte=5)).lex,
            '(id=1) OR (id>=5) AS cnd',
        )

        self.assertEqual(
            SXQLORFilter()(Q(id__eq=1) & Q(id__gte=5)).lex,
            '(id=1) AND (id>=5) AS cnd',
        )

        self.assertIn(
            SXQLORFilter()(Q(id__eq=1) & (Q(id__gte=5) | Q(id__lt=4))).lex,
            ("(id>=5) OR (id<4) AND (id=1) AS cnd",
             "(id=1) AND (id>=5) OR (id<4) AS cnd")
        )

    def test_complex_expression(self):
        sxql_inst = SXQLORFilter()(Q(id__eq=1, id__gte=5) | ~Q(counter__lt=20, id__eq=42))
        results = ('(id>=5 AND id=1) OR (id=42 OR counter<20) AS cnd',
                   '(id=1 AND id>=5) OR (id=42 OR counter<20) AS cnd',
                   '(id>=5 AND id=1) OR (counter<20 OR id=42) AS cnd',
                   '(id=1 AND id>=5) OR (counter<20 OR id=42) AS cnd')
        self.assertIn(sxql_inst.lex, results)

    def test_wrong_attrs(self):
        self.assertRaises(SphinxQLSyntaxException, lambda: SXQLORFilter()(Q(counter__between=[1, 5])).lex)


class TestCount(unittest.TestCase):

    def test_basics(self):
        self.assertEqual(Count().lex, 'COUNT(*) AS num')
        self.assertEqual(Count('counter').lex, 'COUNT(DISTINCT counter) AS counter_count')
        self.assertEqual(Count('counter', 'my_alias').lex, 'COUNT(DISTINCT counter) AS my_alias')
        self.assertEqual(Count(alias='my_alias').lex, 'COUNT(*) AS my_alias')

    def test_wrong_attr(self):
        self.assertRaises(SphinxQLSyntaxException, lambda: Count(['counter']).lex)
        self.assertRaises(SphinxQLSyntaxException, lambda: Count(alias='count').lex)


class TestAvg(unittest.TestCase):

    def test_basics(self):
        self.assertEqual(Avg('price').lex, 'AVG(price) AS price_avg')
        self.assertEqual(Avg('price', 'price_mid').lex, 'AVG(price) AS price_mid')

    def test_wrong_attr(self):
        self.assertRaises(SphinxQLSyntaxException, lambda: Avg(['counter']).lex)
        self.assertRaises(SphinxQLSyntaxException, lambda: Avg('counter', 154).lex)


class TestMin(unittest.TestCase):

    def test_basics(self):
        self.assertEqual(Min('price').lex, 'MIN(price) AS price_min')
        self.assertEqual(Min('price', 'minimal').lex, 'MIN(price) AS minimal')

    def test_wrong_attr(self):
        self.assertRaises(SphinxQLSyntaxException, lambda: Min(['price']).lex)
        self.assertRaises(SphinxQLSyntaxException, lambda: Min('price', 154).lex)


class TestMax(unittest.TestCase):

    def test_basics(self):
        self.assertEqual(Max('price').lex, 'MAX(price) AS price_max')
        self.assertEqual(Max('price', 'maximum').lex, 'MAX(price) AS maximum')

    def test_wrong_attr(self):
        self.assertRaises(SphinxQLSyntaxException, lambda: Max(['price']).lex)


class TestSum(unittest.TestCase):

    def test_basics(self):
        self.assertEqual(Sum('counter').lex, 'SUM(counter) AS counter_sum')
        self.assertEqual(Sum('counter', 'summary').lex, 'SUM(counter) AS summary')

    def test_wrong_attr(self):
        self.assertRaises(SphinxQLSyntaxException, lambda: Sum(['counter']).lex)
        self.assertRaises(SphinxQLSyntaxException, lambda: Sum('counter', 154).lex)


class TestSXQLSnippets(unittest.TestCase):

    def test_basics(self):
        sxql_inst = SXQLSnippets('index', data=['only good news'], query='Good News')
        self.assertEqual(sxql_inst.lex, "CALL SNIPPETS(('only good news'), 'index', 'Good News')")

    def test_with_options_1(self):
        snippet_options = {'limit': 320,
                           'allow_empty': True,
                           }
        possible_options_ordering = ["320 AS limit, 1 AS allow_empty", "1 AS allow_empty, 320 AS limit"]
        sxql_inst = SXQLSnippets('index', data=['only good news'], query='Good News', options=snippet_options)
        possible_queries = ["CALL SNIPPETS(('only good news'), 'index', 'Good News', {opts})".format(opts=opts)
                            for opts in possible_options_ordering]
        self.assertTrue(sxql_inst.lex in possible_queries)

    def test_with_options_2(self):
        snippet_options = {'before_match': '<strong>',
                           'after_match': '</strong>',
                           }
        possible_options_ordering = ["'<strong>' AS before_match, '</strong>' AS after_match",
                                     "'</strong>' AS after_match, '<strong>' AS before_match"]
        sxql_inst = SXQLSnippets('index', data=['only good news'], query='Good News', options=snippet_options)
        possible_queries = ["CALL SNIPPETS(('only good news'), 'index', 'Good News', {opts})".format(opts=opts)
                            for opts in possible_options_ordering]
        self.assertTrue(sxql_inst.lex in possible_queries)

    def test_wrong_usage(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: SXQLSnippets(['good news and bad news', 'only good news'], 'index', 'Good News').lex,
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: SXQLSnippets('index', 'Good News', ['good news and bad news', 'only good news']).lex,
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: SXQLSnippets('index', 'Good News', {}, ['good news and bad news', 'only good news']).lex,
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: SXQLSnippets('index', 42, 'only good news').lex,
        )

    def test_wrong_options_param(self):
        wrong_param_snippet_options = {'before_match': '<strong>',
                                       'aftermatch': '</strong>',
                                       }
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: SXQLSnippets('index', data=['only good news'],
                                          query='Good News',
                                          options=wrong_param_snippet_options).lex,
        )

        wrong_value_snippet_options = {'allow_empty': 12}
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: SXQLSnippets('index', data=['only good news'],
                                          query='Good News',
                                          options=wrong_value_snippet_options).lex,
        )

        wrong_value_snippet_options = {'html_strip_mode': 'wrong_mode'}
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: SXQLSnippets('index', data=['only good news'],
                                          query='Good News',
                                          options=wrong_value_snippet_options).lex,
        )

    def test_quotes_escaping(self):
        sxql_inst_1 = SXQLSnippets('index', data=["only l'amour", "l'oreal"], query="L'amour")
        self.assertEqual(sxql_inst_1.lex, "CALL SNIPPETS(('only l\\'amour', 'l\\'oreal'), 'index', 'L\\'amour')")

    def test_string_as_data(self):
        sxql_inst = SXQLSnippets('index', data='only good news', query='Good News')
        self.assertEqual(sxql_inst.lex, "CALL SNIPPETS(('only good news'), 'index', 'Good News')")
