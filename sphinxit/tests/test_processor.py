# coding=utf-8
from __future__ import unicode_literals
import datetime

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sphinxit.core.nodes import Count, OR, RawAttr
from sphinxit.core.processor import Search, Snippet


class SearchConfig(object):
    DEBUG = False
    WITH_META = True
    WITH_STATUS = True
    SEARCHD_CONNECTION = {
        'host': '127.0.0.1',
        'port': 9306,
    }


class TestSearch(unittest.TestCase):

    def test_simple(self):
        search = Search(indexes=['company'], config=SearchConfig)
        search = search.match('ТНК')

    def test_with_select(self):
        search = Search(indexes=['company'], config=SearchConfig)
        search = search.select('id', 'date_created')
        search = search.match('ТНК')

    def test_with_or_filters(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('ТНК').filter(OR(id__gte=100, id__eq=1))

    def test_with_params(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('ТНК').limit(0, 100).order_by('name', 'desc')

    def test_with_options(self):
        search = Search(['company'], config=SearchConfig)
        search = (
            search
            .match('ТНК')
            .select('id', 'name')
            .options(
                ranker='proximity',
                max_matches=100,
                field_weights={'name': 100},
            )
            .order_by('name', 'desc')
        )

    def test_with_double_match(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('ТНК').match('ОАО')

    def test_with_time_filter(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('ТНК').filter(date_created__lte=datetime.date.today())

    def test_with_raw_attr(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('ТНК').select(RawAttr('@weight*10', 'skey'))

    def test_update_syntax(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('ТНК').update(products=(5,2)).filter(id__gt=1)

    def test_with_grouping(self):
        search = Search(['company'], config=SearchConfig)
        search = search.match('ТНК').select(Count()).group_by('date_created')

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
