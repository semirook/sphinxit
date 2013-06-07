"""
    sphinxit.search
    ~~~~~~~~~~~~~~~

    Implements SphinxQL expression processing.

    :copyright: (c) 2012 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import unicode_literals
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from copy import deepcopy

import six

from sphinxit.core.helpers import sparse_free_sequence
from sphinxit.core.nodes import (
    SelectFromContainer,
    AggregateObject,
    UpdateSetNode,
    FiltersContainer,
    LimitNode,
    GroupByNode,
    WithinGroupOrderByNode,
    OrderByContainer,
    OptionsContainer,
    OR,
    SnippetsOptionsContainer,
    SnippetsQueryNode,
    RawAttr
)
from sphinxit.core.mixins import ConfigMixin
from sphinxit.core.constants import NODES_ORDER
from sphinxit.core.connector import SphinxConnector


class LazySelectTree(ConfigMixin):

    def __init__(self, indexes):
        self._indexes = indexes
        self._nodes = OrderedDict([
            ('SelectFrom', None),
            ('UpdateSet', None),
            ('Where', None),
            ('GroupBy', None),
            ('OrderBy', None),
            ('WithinGroupOrderBy', None),
            ('Limit', None),
            ('Options', None),
        ])
        super(LazySelectTree, self).__init__()

    def __bool__(self):
        return bool(self._nodes['SelectFrom'] or self._nodes['UpdateSet'])

    def copy(self):
        new_tree = LazySelectTree(self._indexes).with_config(self.config)
        new_tree._indexes = self._indexes[:]
        new_tree._nodes = deepcopy(self._nodes)
        return new_tree

    @property
    def SelectFrom(self):
        if self._nodes['SelectFrom'] is None:
            select_container = SelectFromContainer(indexes=self._indexes).with_config(self.config)
            self._nodes['SelectFrom'] = select_container
        return self._nodes['SelectFrom']

    @property
    def Where(self):
        if self._nodes['Where'] is None:
            filters_container = FiltersContainer().with_config(self.config)
            self._nodes['Where'] = filters_container
        return self._nodes['Where']

    @property
    def GroupBy(self):
        if self._nodes['GroupBy'] is None:
            group_by_node = GroupByNode().with_config(self.config)
            self._nodes['GroupBy'] = group_by_node
        return self._nodes['GroupBy']

    @property
    def OrderBy(self):
        if self._nodes['OrderBy'] is None:
            order_by_container = OrderByContainer().with_config(self.config)
            self._nodes['OrderBy'] = order_by_container
        return self._nodes['OrderBy']

    @property
    def WithinGroupOrderBy(self):
        if self._nodes['WithinGroupOrderBy'] is None:
            within_group_order_by_node = WithinGroupOrderByNode().with_config(self.config)
            self._nodes['WithinGroupOrderBy'] = within_group_order_by_node
        return self._nodes['WithinGroupOrderBy']

    @property
    def Limit(self):
        if self._nodes['Limit'] is None:
            self._nodes['Limit'] = LimitNode().with_config(self.config)
        return self._nodes['Limit']

    @property
    def Options(self):
        if self._nodes['Options'] is None:
            options_container = OptionsContainer().with_config(self.config)
            self._nodes['Options'] = options_container
        return self._nodes['Options']

    @property
    def UpdateSet(self):
        if self._nodes['UpdateSet'] is None:
            update_set_node = UpdateSetNode(indexes=self._indexes).with_config(self.config)
            self._nodes['UpdateSet'] = update_set_node
        return self._nodes['UpdateSet']

    def is_update(self):
        return self._nodes['UpdateSet'] is not None

    def get_select_nodes(self):
        if self._nodes['SelectFrom'] is None:
            select_container = SelectFromContainer(indexes=self._indexes).with_config(self.config)
            self._nodes['SelectFrom'] = select_container

        return [self._nodes[n] for n in NODES_ORDER.select]

    def get_update_nodes(self):
        return [self._nodes[n] for n in NODES_ORDER.update]


class LazySnippetsTree(ConfigMixin):
    _template = 'CALL SNIPPETS ({conditions})'

    def __init__(self, index):
        self._index = index
        self._snippets_syntax = OrderedDict([
            ('SnippetQuery', None),
            ('Options', None),
        ])
        super(LazySnippetsTree, self).__init__()

    def __bool__(self):
        return bool(self._snippets_syntax['SnippetQuery'])

    @property
    def SnippetQuery(self):
        if self._snippets_syntax['SnippetQuery'] is None:
            self._snippets_syntax['SnippetQuery'] = (
                SnippetsQueryNode(index=self._index).with_config(self.config)
            )
        return self._snippets_syntax['SnippetQuery']

    @property
    def Options(self):
        if self._snippets_syntax['Options'] is None:
            self._snippets_syntax['Options'] = (
                SnippetsOptionsContainer().with_config(self.config)
            )
        return self._snippets_syntax['Options']

    def lex(self):
        return self._template.format(
            conditions=', '.join([
                x.lex()
                for x in sparse_free_sequence(self._snippets_syntax.values())
            ])
        )


def copy_tree(method):
    def wrapper(self, *args, **kwargs):
        self_copy = self.__class__(self.indexes, self.config, self.connector)
        self_copy._nodes = self._nodes.copy()
        return method(self_copy, *args, **kwargs)
    return wrapper


class Search(ConfigMixin):

    def __init__(self, indexes, config, connector=None):
        super(Search, self).__init__()
        self._nodes = LazySelectTree(indexes=indexes).with_config(config)
        self.indexes = indexes
        self.config = config
        self.connector = connector or SphinxConnector(config)

    @copy_tree
    def select(self, *args, **kwargs):
        if args:
            for field in args:
                if isinstance(field, six.string_types):
                    self._nodes.SelectFrom.add_field(field)
                if isinstance(field, (tuple, list)) and len(field) == 2:
                    field, alias = field
                    self._nodes.SelectFrom.add_alias(field, alias)
                if isinstance(field, AggregateObject):
                    self._nodes.SelectFrom.add_aggregation(field)
                if isinstance(field, RawAttr):
                    self._nodes.SelectFrom.add_raw_attr(field)
        if kwargs:
            for field, alias in kwargs.items():
                self._nodes.SelectFrom.add_alias(field, alias)

        return self

    @copy_tree
    def update(self, **kwargs):
        if kwargs:
            for field, value in kwargs.items():
                self._nodes.UpdateSet.update(field, value)
        return self

    @copy_tree
    def match(self, query, raw=False):
        if not raw:
            self._nodes.Where.add_query(query)
        else:
            self._nodes.Where.add_raw_query(query)

        return self

    @copy_tree
    def filter(self, *args, **kwargs):
        if args:
            for cond in args:
                if isinstance(cond, OR):
                    self._nodes.SelectFrom.add_or(cond)
                    self._nodes.Where.add_condition('cnd__gte', 0)
        if kwargs:
            self._nodes.Where.add_conditions(**kwargs)

        return self

    @copy_tree
    def limit(self, offset=None, limit=None):
        self._nodes.Limit.set_range(offset, limit)
        return self

    @copy_tree
    def group_by(self, field):
        self._nodes.GroupBy.by_field(field)
        return self

    @copy_tree
    def within_group_order_by(self, field, ordering=None):
        self._nodes.WithinGroupOrderBy.by_field(field, ordering)
        return self

    @copy_tree
    def order_by(self, field, ordering=None):
        self._nodes.OrderBy.by_field(field, ordering)
        return self

    @copy_tree
    def options(self, **kwargs):
        self._nodes.Options.set_options(**kwargs)
        return self

    def lex(self):
        if self._nodes.is_update():
            actual_nodes = self._nodes.get_update_nodes()
        else:
            actual_nodes = self._nodes.get_select_nodes()

        return ' '.join([
            x.lex() for x in sparse_free_sequence(actual_nodes)
        ])

    def ask(self, with_meta=False, with_status=False):
        return self.connector.execute(sxql_query=self.lex())


class Snippet(ConfigMixin):

    def __init__(self, index=None, config=None, connector=None):
        super(Snippet, self).__init__()
        self._snippets_tree = LazySnippetsTree(index=index).with_config(config)
        self.index = index
        self.config = config
        self.connector = connector or SphinxConnector(config)

    def from_data(self, *args):
        self._snippets_tree.SnippetQuery.add_data(*args)
        return self

    def for_query(self, query):
        self._snippets_tree.SnippetQuery.add_query(query)
        return self

    def options(self, **kwargs):
        self._snippets_tree.Options.set_options(**kwargs)
        return self

    def lex(self):
        return self._snippets_tree.lex()

    def ask(self):
        return self.connector.execute(
            sxql_query=self.lex(),
            no_extra=True,
        )
