from __future__ import unicode_literals

import random
from sphinxit.core.constants import RESERVED_KEYWORDS

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sphinxit.core.nodes import (
    OR,
    Avg,
    Min,
    Max,
    Sum,
    Count,
    SnippetsQueryNode
)


class DebugConfig(object):
    DEBUG = True


class ProductionConfig(object):
    DEBUG = False


ORSoft = lambda **kwargs: OR(**kwargs).with_config(ProductionConfig)
ORStrict = lambda **kwargs: OR(**kwargs).with_config(DebugConfig)

class TestORNode(unittest.TestCase):

    def test_self(self):
        or_ = ORSoft(age__gte=14)
        self.assertEqual(or_.lex(), '(age>=14)')

    def test_double_self(self):
        or_ = ORSoft(age__gte=14, age__eq=3)
        possible_results = ('(age>=14 OR age=3)', '(age=3 OR age>=14)')
        self.assertIn(or_.lex(), possible_results)

    def test_and_join(self):
        or_ = (
            OR(age__gte=14, age__eq=3)
            & OR(rank__eq=1)
            & OR(rank__eq=2)
            | OR(count__eq=1, count__lte=100, count__between=(1, 10))
        ).with_config(ProductionConfig)
        possible_results = (
            u'(age=3 OR age>=14) AND (rank=1) AND (rank=2) OR (count=1 OR count<=100)',
            u'(age=3 OR age>=14) AND (rank=1) AND (rank=2) OR (count<=100 OR count=1)',
            u'(age>=14 OR age=3) AND (rank=1) AND (rank=2) OR (count=1 OR count<=100)',
            u'(age>=14 OR age=3) AND (rank=1) AND (rank=2) OR (count<=100 OR count=1)',
        )
        self.assertIn(or_.lex(), possible_results)

    def test_or_join(self):
        or_ = (
            OR(age__gte=14, age__eq=3) |
            OR(count__eq=1, count__gte=100, count__between=(1, 10))
        ).with_config(ProductionConfig)
        possible_results = (
            '(age=3 OR age>=14) OR (count=1 OR count>=100)',
            '(age=3 OR age>=14) OR (count>=100 OR count=1)',
            '(age>=14 OR age=3) OR (count=1 OR count>=100)',
            '(age>=14 OR age=3) OR (count>=100 OR count=1)',
        )
        self.assertIn(or_.lex(), possible_results)


AvgSoft = lambda *args, **kwargs: Avg(*args, **kwargs).with_config(ProductionConfig).lex()
AvgStrict = lambda *args, **kwargs: Avg(*args, **kwargs).with_config(DebugConfig).lex()

class TestAvg(unittest.TestCase):

    def test_avg_empty(self):
        self.assertFalse(AvgSoft())

    def test_avg_partly_empty(self):
        self.assertEqual(AvgSoft(field='name'), 'AVG(name) AS name_avg')

    def test_avg_partly_empty_with_alias(self):
        self.assertFalse(AvgSoft(alias='name'))

    def test_avg_complete(self):
        self.assertEqual(
            AvgSoft(field='name', alias='another_name'),
            'AVG(name) AS another_name'
        )


MinSoft = lambda *args, **kwargs: Min(*args, **kwargs).with_config(ProductionConfig).lex()
MinStrict = lambda *args, **kwargs: Min(*args, **kwargs).with_config(DebugConfig).lex()

class TestMin(unittest.TestCase):

    def test_min_empty(self):
        self.assertFalse(MinSoft())

    def test_min_partly_empty(self):
        self.assertEqual(MinSoft(field='name'), 'MIN(name) AS name_min')

    def test_min_partly_empty_with_alias(self):
        self.assertFalse(MinSoft(alias='name'))

    def test_min_complete(self):
        self.assertEqual(
            MinSoft(field='name', alias='another_name'),
            'MIN(name) AS another_name'
        )


MaxSoft = lambda *args, **kwargs: Max(*args, **kwargs).with_config(ProductionConfig).lex()
MaxStrict = lambda *args, **kwargs: Max(*args, **kwargs).with_config(DebugConfig).lex()

class TestMax(unittest.TestCase):

    def test_max_empty(self):
        self.assertFalse(MaxSoft())

    def test_max_partly_empty(self):
        self.assertEqual(MaxSoft(field='name'), 'MAX(name) AS name_max')

    def test_max_partly_empty_with_alias(self):
        self.assertFalse(MaxSoft(alias='name'))

    def test_max_complete(self):
        self.assertEqual(
            MaxSoft(field='name', alias='another_name'),
            'MAX(name) AS another_name'
        )


SumSoft = lambda *args, **kwargs: Sum(*args, **kwargs).with_config(ProductionConfig).lex()
SumStrict = lambda *args, **kwargs: Sum(*args, **kwargs).with_config(DebugConfig).lex()

class TestSum(unittest.TestCase):

    def test_sum_empty(self):
        self.assertFalse(SumSoft())

    def test_sum_partly_empty(self):
        self.assertEqual(SumSoft(field='name'), 'SUM(name) AS name_sum')

    def test_sum_partly_empty_with_alias(self):
        self.assertFalse(SumSoft(alias='name'))

    def test_sum_complete(self):
        self.assertEqual(
            SumSoft(field='name', alias='another_name'),
            'SUM(name) AS another_name'
        )


CountSoft = lambda *args, **kwargs: Count(*args, **kwargs).with_config(ProductionConfig)
CountStrict = lambda *args, **kwargs: Count(*args, **kwargs).with_config(DebugConfig)

class TestCount(unittest.TestCase):

    def test_count_empty(self):
        self.assertEqual(CountSoft().lex(), 'COUNT(*) AS num')

    def test_count_with_alias(self):
        self.assertEqual(CountSoft(alias='counter').lex(), 'COUNT(*) AS counter')

    def test_count_with_field(self):
        self.assertEqual(
            CountSoft(field='age').lex(),
            'COUNT(DISTINCT age) AS age_count'
        )

    def test_count_complete(self):
        self.assertEqual(
            CountSoft(field='age', alias='age_num').lex(),
            'COUNT(DISTINCT age) AS age_num'
        )

    def test_count_with_invalid_field(self):
        self.assertFalse(
            CountSoft(field=random.choice(RESERVED_KEYWORDS), alias='alias').lex(),
        )

    def test_count_with_invalid_alias(self):
        self.assertFalse(
            CountSoft(field='age', alias=random.choice(RESERVED_KEYWORDS)).lex(),
        )


SnippetsQueryNodeSoft = lambda *args, **kwargs: SnippetsQueryNode(*args, **kwargs).with_config(ProductionConfig)
SnippetsQueryNodeStrict = lambda *args, **kwargs: SnippetsQueryNode(*args, **kwargs).with_config(DebugConfig)

class TestSnippetsQueryNode(unittest.TestCase):

    def test_valid_attrs(self):
        node = (
            SnippetsQueryNodeSoft(index='index_name')
            .add_data('me amore sphinx')
            .add_query('me amore')
        )
        self.assertEqual(
            node.lex(),
            "'me amore sphinx', 'index_name', 'me amore'"
        )

    def test_valid_extended_data_attrs(self):
        node = (
            SnippetsQueryNodeSoft(index='index_name')
            .add_data('me amore sphinx', 'me amore python')
            .add_query('me amore')
        )
        self.assertEqual(
            node.lex(),
            "('me amore sphinx', 'me amore python'), 'index_name', 'me amore'"
        )

    def test_valid_extended_query_attrs(self):
        node = (
            SnippetsQueryNodeSoft(index='index_name')
            .add_data('me amore', 'me amore python')
            .add_query('me amore')
            .add_query('python')
        )
        self.assertEqual(
            node.lex(),
            "('me amore', 'me amore python'), 'index_name', 'me amore python'"
        )

    def test_valid_extended_attrs(self):
        node = (
            SnippetsQueryNodeSoft(index='index_name')
            .add_data('me amore', 'me amore python')
            .add_data('me amore python')
            .add_query('me amore')
            .add_query('me amore')
            .add_query('python')
        )
        self.assertEqual(
            node.lex(),
            "('me amore', 'me amore python'), 'index_name', 'me amore python'"
        )

    def test_incomplete_attrs(self):
        self.assertEqual(SnippetsQueryNodeSoft().lex(), '')
        self.assertEqual(SnippetsQueryNodeSoft(index='index_name').lex(), '')
        self.assertEqual(
            SnippetsQueryNodeSoft(index='index_name').add_data('me amore').lex(), ''
        )
        self.assertEqual(
            SnippetsQueryNodeSoft(index='index_name').add_query('python').lex(), ''
        )

    def test_partly_invalid_data(self):
        node = (
            SnippetsQueryNodeSoft(index='index_name')
            .add_data('me amore sphinx', None, 42)
            .add_query('amore')
        )
        self.assertEqual(node.lex(), "'me amore sphinx', 'index_name', 'amore'")

    def test_invalid_data(self):
        node = (
            SnippetsQueryNodeSoft(index='index_name')
            .add_data(None, 42, object, [''], '   ')
            .add_query('   ')
            .add_query('query')
        )
        self.assertEqual(node.lex(), '')
