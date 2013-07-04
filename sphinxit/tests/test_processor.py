# coding=utf-8
from __future__ import unicode_literals
import datetime

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sphinxit.core.nodes import Count, OR, RawAttr
from sphinxit.core.processor import Search, Snippet
from sphinxit.core.helpers import unix_timestamp, BaseSearchConfig


class SearchConfig(BaseSearchConfig):
    WITH_STATUS = False


class TestSearch(unittest.TestCase):

    def test_simple(self):
        search = Search(indexes=['company'], config=SearchConfig)
        search = search.match('Yandex')
        self.assertEqual(
            search.lex(),
            "SELECT * FROM company WHERE MATCH('Yandex')"
        )

    def test_mutability(self):
        search = Search(indexes=['company'], config=SearchConfig)
        search.match('Yandex')
        self.assertEqual(
            search.lex(),
            "SELECT * FROM company"
        )
        search = search.match('Yandex')
        self.assertEqual(
            search.lex(),
            "SELECT * FROM company WHERE MATCH('Yandex')"
        )

    def test_with_select(self):
        search = Search(indexes=['company'], config=SearchConfig)
        search = search.select('id', 'date_created')
        search = search.match('Yandex')
        self.assertEqual(
            search.lex(),
            "SELECT id, date_created FROM company WHERE MATCH('Yandex')"
        )

    def test_with_or_filters(self):
        correct_qls = [
            "SELECT *, (id>=100 OR id=1) AS cnd FROM company WHERE MATCH('Yandex') AND cnd>0",
            "SELECT *, (id=1 OR id>=100) AS cnd FROM company WHERE MATCH('Yandex') AND cnd>0",
        ]
        search = Search(['company'], config=SearchConfig)
        search = search.match('Yandex').filter(OR(id__gte=100, id__eq=1))
        self.assertIn(search.lex(), correct_qls)

    def test_with_or_filters_and_fields(self):
        correct_qls = [
            "SELECT id, (id>=100 OR id=1) AS cnd FROM company WHERE MATCH('Yandex') AND cnd>0",
            "SELECT id, (id=1 OR id>=0) AS cnd FROM company WHERE MATCH('Yandex') AND cnd>0",
        ]
        search = Search(['company'], config=SearchConfig).select('id')
        search = search.match('Yandex').filter(OR(id__gte=100, id__eq=1))
        self.assertIn(search.lex(), correct_qls)

    def test_with_params(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('Yandex').limit(0, 100).order_by('name', 'desc')
        self.assertEqual(
            search.lex(),
            "SELECT * FROM company WHERE MATCH('Yandex') ORDER BY name DESC LIMIT 0,100"
        )

    def test_with_options(self):
        search = Search(['company'], config=SearchConfig)
        search = (
            search
            .match('Yandex')
            .select('id', 'name')
            .options(
                ranker='proximity',
                max_matches=100,
                field_weights={'name': 100},
            )
            .order_by('name', 'desc')
        )
        correct_options_qls = [
            "max_matches=100, ranker=proximity, field_weights=(name=100)",
            "max_matches=100, field_weights=(name=100), ranker=proximity",
            "ranker=proximity, field_weights=(name=100), max_matches=100",
            "ranker=proximity, max_matches=100, field_weights=(name=100)",
            "field_weights=(name=100), max_matches=100, ranker=proximity",
            "field_weights=(name=100), ranker=proximity, max_matches=100",
        ]
        correct_qls = [
            " ".join((
                "SELECT id, name FROM company WHERE MATCH('Yandex') ORDER BY name DESC OPTION",
                opt
            ))
            for opt in correct_options_qls
        ]
        self.assertIn(search.lex(), correct_qls)

    def test_with_double_match(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('ОАО').match('ТНК')
        self.assertEqual(
            search.lex(),
            "SELECT * FROM company WHERE MATCH('ОАО ТНК')"
        )

    def test_with_time_filter(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('Yandex').filter(date_created__lte=datetime.date.today())
        today = datetime.date.today()
        sxql = (
            "SELECT * FROM company WHERE MATCH('Yandex') "
            "AND date_created<=%s" % unix_timestamp(today)
        )
        self.assertEqual(search.lex(), sxql)

    def test_with_raw_attr(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('Yandex').select(RawAttr('@weight*10', 'skey'))
        self.assertEqual(
            search.lex(),
            "SELECT @weight*10 AS skey FROM company WHERE MATCH('Yandex')"
        )

    def test_update_syntax(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('Yandex').update(products=(5,2)).filter(id__gt=1)
        self.assertEqual(
            search.lex(),
            "UPDATE company SET products=(5,2) WHERE MATCH('Yandex') AND id>1"
        )

    def test_with_grouping(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('Yandex').select(Count()).group_by('date_created')
        self.assertEqual(
            search.lex(),
            "SELECT COUNT(*) AS num FROM company WHERE MATCH('Yandex') GROUP BY date_created"
        )

    def test_with_multiindex(self):
        search = Search(
            indexes=['company', 'company_delta'],
            config=SearchConfig
        )
        search = search.filter(id__gte=100)
        self.assertEqual(
            search.lex(),
            "SELECT * FROM company, company_delta WHERE id>=100"
        )


class TestSnippets(unittest.TestCase):

    def test_simple(self):
        snippets = (
            Snippet(index='company', config=SearchConfig)
            .for_query("Me amore")
            .from_data("amore")
        )
        self.assertEqual(
            snippets.lex(),
            "CALL SNIPPETS ('amore', 'company', 'Me amore')"
        )

    def test_extended_1(self):
        snippets = (
            Snippet(index='company', config=SearchConfig)
            .for_query("Me amore")
            .from_data("amore", "amore mia")
        )
        self.assertEqual(
            snippets.lex(),
            "CALL SNIPPETS (('amore', 'amore mia'), 'company', 'Me amore')"
        )

    def test_extended_2(self):
        snippets = (
            Snippet(index='company', config=SearchConfig)
            .for_query("Me amore")
            .from_data("amore")
            .from_data("me amore")
        )
        self.assertEqual(
            snippets.lex(),
            "CALL SNIPPETS (('amore', 'me amore'), 'company', 'Me amore')"
        )

    def test_with_options(self):
        snippets = (
            Snippet(index='company', config=SearchConfig)
            .for_query("Me amore")
            .from_data("amore mia")
            .options(before_match='<strong>', after_match='</strong>')
        )
        self.assertEqual(
            snippets.lex(), (
                "CALL SNIPPETS ('amore mia', 'company', 'Me amore', "
                "'<strong>' AS before_match, '</strong>' AS after_match)"
            )
        )
