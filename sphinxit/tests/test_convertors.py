from __future__ import unicode_literals

import random
from datetime import datetime, date

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sphinxit.core.constants import RESERVED_KEYWORDS, ESCAPED_CHARS
from sphinxit.core.exceptions import SphinxQLSyntaxException
from sphinxit.core.helpers import (
    list_of_integers_only,
    int_from_digit,
    sparse_free_sequence,
    unix_timestamp
)
from sphinxit.core.convertors import (
    FilterCtx,
    MatchQueryCtx,
    AliasFieldCtx,
    LimitCtx,
    OrderCtx,
    FieldCtx,
    OptionsCtx,
    UpdateSetCtx,
)


class DebugConfig(object):
    DEBUG = True


class ProductionConfig(object):
    DEBUG = False


class TestListOfIntegersOnlyConverter(unittest.TestCase):

    def test_clean_sequence(self):
        sequence = [1, 2, 3, 4, 5]
        self.assertListEqual(list_of_integers_only(sequence), sequence)

    def test_digit_str_sequence(self):
        sequence = [1, '2', 3, 4, '5']
        self.assertListEqual(list_of_integers_only(sequence), [1, 2, 3, 4, 5])

    def test_str_sequence(self):
        sequence = [1, 'boom', 3, 4, '5']
        self.assertListEqual(list_of_integers_only(sequence), [1, 3, 4, 5])

    def test_str_sequence_strict(self):
        sequence = [1, 'boom', 3, 4, '5']
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: list_of_integers_only(sequence, is_strict=True),
        )


class TestIntFromDigit(unittest.TestCase):

    def test_int(self):
        self.assertEqual(int_from_digit(42), 42)

    def test_digit_str(self):
        self.assertEqual(int_from_digit('42'), 42)

    def test_str(self):
        self.assertIsNone(int_from_digit('boom'))

    def test_str_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: int_from_digit('boom', is_strict=True),
        )


class TestSparseFreeSequence(unittest.TestCase):

    def test_sparse(self):
        dirty_list = ['1', 2, None, '4', '  ', 6, {'key': 'value'}, [], ()]
        self.assertEqual(
            sparse_free_sequence(dirty_list),
            ['1', 2, '4', 6, {'key': 'value'}]
        )


FilterCtxStrict = lambda *args, **kwargs: FilterCtx(*args, **kwargs).with_config(DebugConfig)
FilterCtxSoft = lambda *args, **kwargs: FilterCtx(*args, **kwargs).with_config(ProductionConfig)

class TestFilterCtx(unittest.TestCase):

    def test_eq_non_strict(self):
        with FilterCtxSoft('age__eq', 25) as value:
            self.assertEqual(value, 'age=25')

        with FilterCtxSoft('age__eq', '25') as value:
            self.assertEqual(value, 'age=25')

        with FilterCtxSoft('age__eq', '25d') as value:
            self.assertIsNone(value)

    def test_eq_strict(self):
        with FilterCtxStrict('age__eq', 25) as value:
            self.assertEqual(value, 'age=25')

        with FilterCtxStrict('age__eq', '25') as value:
            self.assertEqual(value, 'age=25')

        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FilterCtxStrict('age__eq', '25d').__enter__()
        )

    def test_neq_non_strict(self):
        with FilterCtxSoft('age__neq', 25) as value:
            self.assertEqual(value, 'age!=25')

        with FilterCtxSoft('age__neq', '25') as value:
            self.assertEqual(value, 'age!=25')

        with FilterCtxSoft('age__neq', '25d') as value:
            self.assertIsNone(value)

    def test_neq_strict(self):
        with FilterCtxStrict('age__neq', 25) as value:
            self.assertEqual(value, 'age!=25')

        with FilterCtxStrict('age__neq', '25') as value:
            self.assertEqual(value, 'age!=25')

        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FilterCtxStrict('age__neq', '25d').__enter__()
        )

    def test_gt_non_strict(self):
        with FilterCtxSoft('age__gt', 25) as value:
            self.assertEqual(value, 'age>25')

        with FilterCtxSoft('age__gt', '25') as value:
            self.assertEqual(value, 'age>25')

        with FilterCtxSoft('age__gt', '25d') as value:
            self.assertIsNone(value)

    def test_gt_strict(self):
        with FilterCtxStrict('age__gt', 25) as value:
            self.assertEqual(value, 'age>25')

        with FilterCtxStrict('age__gt', '25') as value:
            self.assertEqual(value, 'age>25')

        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FilterCtxStrict('age__gt', '25d').__enter__()
        )

    def test_gte_non_strict(self):
        with FilterCtxSoft('age__gte', 25) as value:
            self.assertEqual(value, 'age>=25')

        with FilterCtxSoft('age__gte', '25') as value:
            self.assertEqual(value, 'age>=25')

        with FilterCtxSoft('age__gte', '25d') as value:
            self.assertIsNone(value)

    def test_gte_strict(self):
        with FilterCtxStrict('age__gte', 25) as value:
            self.assertEqual(value, 'age>=25')

        with FilterCtxStrict('age__gte', '25') as value:
            self.assertEqual(value, 'age>=25')

        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FilterCtxStrict('age__gte', '25d').__enter__()
        )

    def test_lt_non_strict(self):
        with FilterCtxSoft('age__lt', 25) as value:
            self.assertEqual(value, 'age<25')

        with FilterCtxSoft('age__lt', '25') as value:
            self.assertEqual(value, 'age<25')

        with FilterCtxSoft('age__lt', '25d') as value:
            self.assertEqual(value, None)

    def test_lt_strict(self):
        with FilterCtxStrict('age__lt', 25) as value:
            self.assertEqual(value, 'age<25')

        with FilterCtxStrict('age__lt', '25') as value:
            self.assertEqual(value, 'age<25')

        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FilterCtxStrict('age__lt', '25d').__enter__()
        )

    def test_lte_non_strict(self):
        with FilterCtxSoft('age__lte', 25) as value:
            self.assertEqual(value, 'age<=25')

        with FilterCtxSoft('age__lte', '25') as value:
            self.assertEqual(value, 'age<=25')

        with FilterCtxSoft('age__lte', '25d') as value:
            self.assertEqual(value, None)

    def test_lte_strict(self):
        with FilterCtxStrict('age__lte', 25) as value:
            self.assertEqual(value, 'age<=25')

        with FilterCtxStrict('age__lte', '25') as value:
            self.assertEqual(value, 'age<=25')

        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FilterCtxStrict('age__lte', '25d').__enter__()
        )

    def test_in_non_strict(self):
        with FilterCtxSoft('age__in', (1, 2, 3)) as value:
            self.assertEqual(value, 'age IN (1,2,3)')

        with FilterCtxSoft('age__in', (1, '2', 3)) as value:
            self.assertEqual(value, 'age IN (1,2,3)')

        with FilterCtxSoft('age__in', (1, '2', 'string', 3, '42d')) as value:
            self.assertEqual(value, 'age IN (1,2,3)')

        with FilterCtxSoft('age__in', []) as value:
            self.assertIsNone(value)

        with FilterCtxSoft('age__in', None) as value:
            self.assertIsNone(value)

    def test_in_strict(self):
        with FilterCtxStrict('age__in', (1, 2, 3)) as value:
            self.assertEqual(value, 'age IN (1,2,3)')

        with FilterCtxStrict('age__in', (1, '2', 3)) as value:
            self.assertEqual(value, 'age IN (1,2,3)')

        with FilterCtxStrict('age__in', []) as value:
            self.assertIsNone(value)

        with FilterCtxStrict('age__in', None) as value:
            self.assertIsNone(value)

        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FilterCtxStrict('age__in', [1, 2, 3, '42d']).__enter__()
        )

    def test_between_non_strict(self):
        with FilterCtxSoft('age__between', (1, 25)) as value:
            self.assertEqual(value, 'age BETWEEN 1 AND 25')

        with FilterCtxSoft('age__between', (1, 25, 35)) as value:
            self.assertIsNone(value)

        with FilterCtxSoft('age__between', (1, '25')) as value:
            self.assertEqual(value, 'age BETWEEN 1 AND 25')

        with FilterCtxSoft('age__between', (1, 'string')) as value:
            self.assertIsNone(value)

        with FilterCtxSoft('age__between', ()) as value:
            self.assertIsNone(value)

    def test_between_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FilterCtxStrict('age__between', (1, 25, 35)).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FilterCtxStrict('age__between', (1, 'string')).__enter__()
        )
        with FilterCtxStrict('age__between', (1, 25)) as value:
            self.assertEqual(value, 'age BETWEEN 1 AND 25')

        with FilterCtxStrict('age__between', ()) as value:
            self.assertIsNone(value)

    def test_invalid_condition(self):
        with FilterCtxSoft('age__range', (1, 25)) as value:
            self.assertIsNone(value)

    def test_invalid_condition_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FilterCtxStrict('age__range', (1, 25)).__enter__()
        )

    def test_datetime_condition(self):
        today_stamp = unix_timestamp(date.today())
        with FilterCtxStrict('age__eq', today_stamp) as value:
            self.assertEqual(value, 'age=%s' % today_stamp)

        now_stamp = unix_timestamp(datetime.now())
        with FilterCtxStrict('age__eq', now_stamp) as value:
            self.assertEqual(value, 'age=%s' % now_stamp)

    def test_float_condition(self):
        with FilterCtxStrict('age__eq', 5.5) as value:
            self.assertEqual(value, 'age=5.5')


MatchQueryCtxSoft = lambda *args, **kwargs: MatchQueryCtx(*args, **kwargs).with_config(ProductionConfig)
MatchQueryCtxStrict = lambda *args, **kwargs: MatchQueryCtx(*args, **kwargs).with_config(DebugConfig)

class TestMatchQueryCtx(unittest.TestCase):

    def test_single_slash(self):
        symbol = random.choice(ESCAPED_CHARS.single_escape)
        with MatchQueryCtxSoft(symbol) as value:
            self.assertEqual(value, r"\{0}".format(symbol))

    def test_double_slash(self):
        symbol = random.choice(ESCAPED_CHARS.double_escape)
        with MatchQueryCtxSoft(symbol) as value:
            self.assertEqual(value, r"\\{0}".format(symbol))

    def test_single_slash_raw(self):
        symbol = random.choice(ESCAPED_CHARS.single_escape)
        with MatchQueryCtxSoft(symbol, raw=True) as value:
            self.assertEqual(value, symbol)

    def test_raw_double_slash(self):
        symbol = random.choice(ESCAPED_CHARS.double_escape)
        with MatchQueryCtxSoft(symbol, raw=True) as value:
            self.assertEqual(value, symbol)

    def test_simple_valid_string(self):
        with MatchQueryCtxSoft('Find me some money') as value:
            self.assertEqual(value, "Find me some money")

    def test_symbol_escape(self):
        with MatchQueryCtxSoft('@full_name ^Roman') as value:
            self.assertEqual(value, r'\\@full_name \\^Roman')

    def test_quotes_escape(self):
        with MatchQueryCtxSoft('"name') as value:
            self.assertEqual(value, r'\\"name')

    def test_quote_escape(self):
        with MatchQueryCtxSoft("l'amour") as value:
            self.assertEqual(value, r"l\'amour")

    def test_raw_query(self):
        mail_query = '@email "semirook@gmail.com"'
        with MatchQueryCtxSoft(mail_query, raw=True) as value:
            self.assertEqual(value, mail_query)

    def test_invalid_query(self):
        with MatchQueryCtxSoft(42) as value:
            self.assertIsNone(value)

        with MatchQueryCtxSoft('') as value:
            self.assertIsNone(value)

        with MatchQueryCtxSoft('   ') as value:
            self.assertIsNone(value)

    def test_invalid_query_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: MatchQueryCtxStrict(42).__enter__()
        )
        with MatchQueryCtxStrict('') as value:
            self.assertIsNone(value)

        with MatchQueryCtxStrict('   ') as value:
            self.assertIsNone(value)


AliasFieldCtxSoft = lambda x, y: AliasFieldCtx(x, y).with_config(ProductionConfig)
AliasFieldCtxStrict = lambda x, y: AliasFieldCtx(x, y).with_config(DebugConfig)

class TestAliasFieldCtx(unittest.TestCase):

    def test_valid_attrs(self):
        with AliasFieldCtxSoft('name', 'another_name') as value:
            self.assertEqual(value, 'name AS another_name')

    def test_valid_attrs_strict(self):
        with AliasFieldCtxStrict('name', 'another_name') as value:
            self.assertEqual(value, 'name AS another_name')

    def test_invalid_attrs(self):
        with AliasFieldCtxSoft('name', 42) as value:
            self.assertIsNone(value)

        with AliasFieldCtxSoft('name', random.choice(RESERVED_KEYWORDS)) as value:
            self.assertIsNone(value)

        with AliasFieldCtxSoft(random.choice(RESERVED_KEYWORDS), 'alias') as value:
            self.assertIsNone(value)

        with AliasFieldCtxSoft('', '') as value:
            self.assertIsNone(value)

        with AliasFieldCtxSoft('   ', '   ') as value:
            self.assertIsNone(value)

    def test_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: AliasFieldCtxStrict('name', 42).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: AliasFieldCtxStrict('name', random.choice(RESERVED_KEYWORDS)).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: AliasFieldCtxStrict(random.choice(RESERVED_KEYWORDS), 'alias').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: AliasFieldCtxStrict('', '').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: AliasFieldCtxStrict('   ', '   ').__enter__()
        )


FieldCtxSoft = lambda field: FieldCtx(field).with_config(ProductionConfig)
FieldCtxStrict = lambda field: FieldCtx(field).with_config(DebugConfig)

class TestFieldCtx(unittest.TestCase):

    def test_valid_attrs(self):
        with FieldCtxSoft('name') as lex:
            self.assertEqual(lex, 'name')

    def test_valid_attrs_strict(self):
        with FieldCtxStrict('name') as lex:
            self.assertEqual(lex, 'name')

    def test_invalid_attrs(self):
        with FieldCtxSoft('') as lex:
            self.assertIsNone(lex)

        with FieldCtxSoft('   ') as lex:
            self.assertIsNone(lex)

        with FieldCtxSoft(random.choice(RESERVED_KEYWORDS)) as lex:
            self.assertIsNone(lex)

    def test_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FieldCtxStrict('').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FieldCtxStrict('   ').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: FieldCtxStrict(random.choice(RESERVED_KEYWORDS)).__enter__()
        )


LimitCtxSoft = lambda x, y: LimitCtx(x, y).with_config(ProductionConfig)
LimitCtxStrict = lambda x, y: LimitCtx(x, y).with_config(DebugConfig)

class TestLimitCtx(unittest.TestCase):

    def test_valid_attrs(self):
        with LimitCtxSoft(0, 100) as lex:
            self.assertEqual([0, 100], lex)

        with LimitCtxSoft(0, '100') as lex:
            self.assertEqual([0, 100], lex)

    def test_invalid_attrs(self):
        with LimitCtxSoft(0, 0) as lex:
            self.assertIsNone(lex)

        with LimitCtxSoft(-2, 100) as lex:
            self.assertIsNone(lex)

        with LimitCtxSoft(0, 'boom') as lex:
            self.assertIsNone(lex)

    def test_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: LimitCtxStrict(0, 0).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: LimitCtxStrict(-2, 100).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: LimitCtxStrict(0, 'boom').__enter__()
        )


OrderCtxSoft = lambda x, y: OrderCtx(x, y).with_config(ProductionConfig)
OrderCtxStrict = lambda x, y: OrderCtx(x, y).with_config(DebugConfig)

class TestOrderCtx(unittest.TestCase):

    def test_valid_attrs(self):
        with OrderCtxSoft('name', 'ASC') as lex:
            self.assertEqual(lex, 'name ASC')

        with OrderCtxSoft('name', 'DESC') as lex:
            self.assertEqual(lex, 'name DESC')

        with OrderCtxSoft('name', 'asc') as lex:
            self.assertEqual(lex, 'name ASC')

        with OrderCtxSoft('name', 'desc') as lex:
            self.assertEqual(lex, 'name DESC')

    def test_invalid_attrs(self):
        with OrderCtxSoft('', 'ASC') as lex:
            self.assertIsNone(lex)

        with OrderCtxSoft('   ', 'ASC') as lex:
            self.assertIsNone(lex)

        with OrderCtxSoft('name', 'DEC') as lex:
            self.assertIsNone(lex)

        with OrderCtxSoft(42, 'ASC') as lex:
            self.assertIsNone(lex)

        with OrderCtxSoft('asc', 'name') as lex:
            self.assertIsNone(lex)

    def test_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OrderCtxStrict('', 'ASC').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OrderCtxStrict('   ', 'ASC').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OrderCtxStrict('name', 'DEC').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OrderCtxStrict(42, 'ASC').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OrderCtxStrict('asc', '').__enter__()
        )


OptionsCtxSoft = lambda x, y: OptionsCtx(x, y).with_config(ProductionConfig)
OptionsCtxStrict = lambda x, y: OptionsCtx(x, y).with_config(DebugConfig)

class TestOptionsCtx(unittest.TestCase):

    def test_get_ranker_valid_attrs(self):
        with OptionsCtxSoft('ranker', 'proximity_bm25') as lex:
            self.assertEqual(lex, 'ranker=proximity_bm25')

        with OptionsCtxSoft('ranker', 'bm25') as lex:
            self.assertEqual(lex, 'ranker=bm25')

        with OptionsCtxSoft('ranker', 'none') as lex:
            self.assertEqual(lex, 'ranker=none')

        with OptionsCtxSoft('ranker', 'wordcount') as lex:
            self.assertEqual(lex, 'ranker=wordcount')

        with OptionsCtxSoft('ranker', 'proximity') as lex:
            self.assertEqual(lex, 'ranker=proximity')

        with OptionsCtxSoft('ranker', 'matchany') as lex:
            self.assertEqual(lex, 'ranker=matchany')

        with OptionsCtxSoft('ranker', 'fieldmask') as lex:
            self.assertEqual(lex, 'ranker=fieldmask')

    def test_get_ranker_invalid_attrs(self):
        with OptionsCtxSoft('ranker', 'yandex') as lex:
            self.assertIsNone(lex)

    def test_get_ranker_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('ranker', 'yandex').__enter__()
        )

    def test_get_max_matches_valid_attrs(self):
        with OptionsCtxSoft('max_matches', 3000) as lex:
            self.assertEqual(lex, 'max_matches=3000')

        with OptionsCtxSoft('max_matches', '3000') as lex:
            self.assertEqual(lex, 'max_matches=3000')

    def test_get_max_matches_invalid_attrs(self):
        with OptionsCtxSoft('max_matches', 0) as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('max_matches', '') as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('max_matches', 'many') as lex:
            self.assertIsNone(lex)

    def test_get_max_matches_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('max_matches', 0).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('max_matches', '').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('max_matches', 'many').__enter__()
        )

    def test_get_cutoff_valid_attrs(self):
        with OptionsCtxSoft('cutoff', 7) as lex:
            self.assertEqual(lex, 'cutoff=7')

        with OptionsCtxSoft('cutoff', '7') as lex:
            self.assertEqual(lex, 'cutoff=7')

    def test_get_cutoff_invalid_attrs(self):
        with OptionsCtxSoft('cutoff', 0) as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('cutoff', '') as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('cutoff', 'many') as lex:
            self.assertIsNone(lex)

    def test_get_cutoff_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('cutoff', 0).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('cutoff', '').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('cutoff', 'many').__enter__()
        )

    def test_max_query_time_valid_attrs(self):
        with OptionsCtxSoft('max_query_time', 100) as lex:
            self.assertEqual(lex, 'max_query_time=100')

        with OptionsCtxSoft('max_query_time', '100') as lex:
            self.assertEqual(lex, 'max_query_time=100')

    def test_max_query_time_invalid_attrs(self):
        with OptionsCtxSoft('max_query_time', '') as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('max_query_time', 0) as lex:
            self.assertIsNone(lex)

    def test_max_query_time_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('max_query_time', '').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('max_query_time', 0).__enter__()
        )

    def test_retry_count_valid_attrs(self):
        with OptionsCtxSoft('retry_count', 3) as lex:
            self.assertEqual(lex, 'retry_count=3')

        with OptionsCtxSoft('retry_count', '3') as lex:
            self.assertEqual(lex, 'retry_count=3')

    def test_retry_count_invalid_attrs(self):
        with OptionsCtxSoft('retry_count', '') as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('retry_count', 0) as lex:
            self.assertIsNone(lex)

    def test_retry_count_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('retry_count', '').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('retry_count', 0).__enter__()
        )

    def test_retry_delay_valid_attrs(self):
        with OptionsCtxSoft('retry_delay', 3) as lex:
            self.assertEqual(lex, 'retry_delay=3')

        with OptionsCtxSoft('retry_delay', '3') as lex:
            self.assertEqual(lex, 'retry_delay=3')

    def test_retry_delay_invalid_attrs(self):
        with OptionsCtxSoft('retry_delay', '') as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('retry_delay', 0) as lex:
            self.assertIsNone(lex)

    def test_retry_delay_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('retry_delay', '').__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('retry_delay', 0).__enter__()
        )

    def test_field_weights_valid_attrs(self):
        with OptionsCtxSoft('field_weights', {'title': 100, 'body': 50}) as lex:
            self.assertTrue(lex in [
                'field_weights=(body=50, title=100)',
                'field_weights=(title=100, body=50)'
            ])
        with OptionsCtxSoft('field_weights', {'title': '100', 'body': '50'}) as lex:
            self.assertTrue(lex in [
                'field_weights=(body=50, title=100)',
                'field_weights=(title=100, body=50)'
            ])

    def test_field_weights_invalid_attrs(self):
        with OptionsCtxSoft('field_weights', ('title', 0)) as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('field_weights', 100) as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('field_weights', {'title': 10, 'body': 0}) as lex:
            self.assertEqual(lex, 'field_weights=(title=10)')

    def test_field_weights_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('field_weights', ('title', 0)).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('field_weights', 100).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('field_weights', {'title': 10, 'body': 0}).__enter__()
        )

    def test_index_weights_valid_attrs(self):
        with OptionsCtxSoft('index_weights', {'company': 1, 'company_delta': 2}) as lex:
            self.assertTrue(lex in [
                'index_weights=(company=1, company_delta=2)',
                'index_weights=(company_delta=2, company=1)'
            ])
        with OptionsCtxSoft('index_weights', {'company': '1', 'company_delta': '2'}) as lex:
            self.assertTrue(lex in [
                'index_weights=(company=1, company_delta=2)',
                'index_weights=(company_delta=2, company=1)'
            ])

    def test_index_weights_invalid_attrs(self):
        with OptionsCtxSoft('index_weights', ('company', 0)) as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('index_weights', 100) as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('index_weights', {'company': 1, 'company_delta': 0}) as lex:
            self.assertEqual(lex, 'index_weights=(company=1)')

    def test_index_weights_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('index_weights', ('company', 0)).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('index_weights', 100).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('index_weights', {'company': 1, 'company_delta': 0}).__enter__()
        )

    def test_reverse_scan_valid_attrs(self):
        with OptionsCtxSoft('reverse_scan', True) as lex:
            self.assertEqual(lex, 'reverse_scan=1')

        with OptionsCtxSoft('reverse_scan', False) as lex:
            self.assertEqual(lex, 'reverse_scan=0')

    def test_reverse_scan_invalid_attrs(self):
        with OptionsCtxSoft('reverse_scan', 1) as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('reverse_scan', 0) as lex:
            self.assertIsNone(lex)

        with OptionsCtxSoft('reverse_scan', '1') as lex:
            self.assertIsNone(lex)

    def test_reverse_scan_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('reverse_scan', 1).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('reverse_scan', 0).__enter__()
        )
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('reverse_scan', '0').__enter__()
        )

    def test_comment_valid_attrs(self):
        with OptionsCtxSoft('comment', 'Comment text') as lex:
            self.assertEqual(lex, 'comment=Comment text')

    def test_comment_invalid_attrs(self):
        with OptionsCtxSoft('comment', 42) as lex:
            self.assertIsNone(lex)

    def test_comment_invalid_attrs_strict(self):
        self.assertRaises(
            SphinxQLSyntaxException,
            lambda: OptionsCtxStrict('comment', 42).__enter__()
        )


UpdateSetCtxSoft = lambda x, y: UpdateSetCtx(x, y).with_config(ProductionConfig)
UpdateSetCtxStrict = lambda x, y: UpdateSetCtx(x, y).with_config(DebugConfig)

class TestUpdateSetCtx(unittest.TestCase):

    def test_valid_attrs(self):
        with UpdateSetCtxSoft('intattr', 1000) as lex:
            self.assertEqual(lex, 'intattr=1000')

        with UpdateSetCtxSoft('intattr', '1000') as lex:
            self.assertEqual(lex, 'intattr=1000')

        with UpdateSetCtxSoft('fattr', 100.002) as lex:
            self.assertEqual(lex, 'fattr=100.002')

        with UpdateSetCtxSoft('mvattr', [1, 2, 3]) as lex:
            self.assertEqual(lex, 'mvattr=(1,2,3)')

        with UpdateSetCtxSoft('mvattr', [1, '2', 3]) as lex:
            self.assertEqual(lex, 'mvattr=(1,2,3)')

        with UpdateSetCtxSoft('mvattr', (1, '2', 3)) as lex:
            self.assertEqual(lex, 'mvattr=(1,2,3)')

        with UpdateSetCtxSoft('attr', '') as lex:
            self.assertEqual(lex, 'attr=()')

        with UpdateSetCtxSoft('attr', []) as lex:
            self.assertEqual(lex, 'attr=()')

        with UpdateSetCtxSoft('attr', ()) as lex:
            self.assertEqual(lex, 'attr=()')

        with UpdateSetCtxSoft('attr', None) as lex:
            self.assertEqual(lex, 'attr=()')

    def test_invalid_attrs(self):
        with UpdateSetCtxSoft('', 1000) as lex:
            self.assertIsNone(lex)

        with UpdateSetCtxSoft('attr', 'string_is_not_supported') as lex:
            self.assertIsNone(lex)

        with UpdateSetCtxSoft('attr', ['1', 2, None, 'string']) as lex:
            self.assertEqual(lex, 'attr=(1,2)')
