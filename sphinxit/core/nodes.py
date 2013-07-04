"""
    sphinxit.core.nodes
    ~~~~~~~~~~~~~~~~~~~

    Implements atomic nodes and containers of lexemes.

    :copyright: (c) 2013 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import unicode_literals

from collections import deque

from sphinxit.core.convertors import (
    FilterCtx,
    ORFilterCtx,
    MatchQueryCtx,
    AliasFieldCtx,
    FieldCtx,
    OrderCtx,
    LimitCtx,
    OptionsCtx,
    UpdateSetCtx,
    SnippetsOptionsCtx
)
from sphinxit.core.helpers import (
    sparse_free_sequence,
    string_from_string,
)
from sphinxit.core.exceptions import SphinxQLSyntaxException
from sphinxit.core.mixins import ConfigMixin


class SelectFromContainer(ConfigMixin):
    _joiner = ', '
    _template = 'SELECT {fields} FROM {indexes}'

    def __init__(self, indexes=None):
        super(SelectFromContainer, self).__init__()
        self.indexes = indexes
        self.fields = []
        self.or_fields = []

    def add_alias(self, field, alias):
        with AliasFieldCtx(field, alias).with_config(self.config) as lex:
            if lex and lex not in self.fields:
                self.fields.append(lex)

    def add_field(self, field):
        with FieldCtx(field).with_config(self.config) as lex:
            if lex and lex not in self.fields:
                self.fields.append(lex)

    def add_or(self, or_instance):
        assert isinstance(or_instance, OR), type(or_instance)
        with AliasFieldCtx(
            or_instance.with_config(self.config).lex(), 'cnd'
        ).with_config(self.config) as lex:
            if lex and lex not in self.or_fields:
                self.or_fields.append(lex)

    def add_aggregation(self, agg_instance):
        assert isinstance(agg_instance, AggregateObject), type(agg_instance)
        agg_lex = agg_instance.with_config(self.config).lex()
        if agg_lex and agg_lex not in self.fields:
            self.fields.append(agg_lex)

    def add_raw_attr(self, raw_attr_instance):
        assert isinstance(raw_attr_instance, RawAttr), type(raw_attr_instance)
        raw_lex = raw_attr_instance.with_config(self.config).lex()
        if raw_lex and raw_lex not in self.fields:
            self.fields.append(raw_lex)

    def has_or_fields(self):
        return bool(self.or_fields)

    def lex(self):
        if self.indexes is None:
            raise SphinxQLSyntaxException('No indexes defined to search with')

        lex = self._template.format(
            fields=self._joiner.join((self.fields or ['*']) + self.or_fields),
            indexes=self._joiner.join(self.indexes),
        )
        return lex


class FiltersContainer(ConfigMixin):
    _joiner = ' AND '
    _match_template = "MATCH('{query}')"
    _where_template = 'WHERE {conditions}'

    def __init__(self):
        super(FiltersContainer, self).__init__()
        self.query = []
        self.conditions = []

    def __bool__(self):
        return bool(self.conditions or self.query)

    def add_query(self, query):
        with MatchQueryCtx(query).with_config(self.config) as lex:
            if lex:
                self.query.append(lex)

    def add_raw_query(self, query):
        self.query.append(query)

    def add_condition(self, field, value):
        with FilterCtx(field, value).with_config(self.config) as lex:
            if lex and lex not in self.conditions:
                self.conditions.append(lex)

    def add_conditions(self, **kwargs):
        for field, value in kwargs.items():
            self.add_condition(field, value)

    def lex(self):
        query_lex = ''
        cond_lex = ''
        if self.query:
            query_lex = self._match_template.format(
                query=' '.join(self.query)
            )
        if self.conditions:
            cond_lex = self._joiner.join(self.conditions)

        return self._where_template.format(
            conditions=self._joiner.join(sparse_free_sequence([query_lex, cond_lex]))
        )


class GroupByNode(ConfigMixin):
    _template = 'GROUP BY {field}'

    def __init__(self):
        super(GroupByNode, self).__init__()
        self.field = None

    def __bool__(self):
        return bool(self.field)

    def by_field(self, field):
        if not self:
            with FieldCtx(field).with_config(self.config) as lex:
                if lex:
                    self.field = field

    def lex(self):
        if self:
            return self._template.format(field=self.field)
        return ''


class OrderByContainer(ConfigMixin):
    _joiner = ', '
    _template = 'ORDER BY {orderings}'

    def __init__(self):
        super(OrderByContainer, self).__init__()
        self.orderings = set()

    def __bool__(self):
        return bool(self.orderings)

    def by_field(self, field, direction='ASC'):
        with OrderCtx(field, direction).with_config(self.config) as lex:
            if lex and lex not in self.orderings:
                self.orderings.add(lex)

    def lex(self):
        if self:
            return self._template.format(
                orderings=self._joiner.join(self.orderings)
            )
        return ''


class WithinGroupOrderByNode(ConfigMixin):
    _template = 'WITHIN GROUP ORDER BY {field}'

    def __init__(self):
        super(WithinGroupOrderByNode, self).__init__()
        self.field = None

    def __bool__(self):
        return bool(self.field)

    def by_field(self, field, direction='ASC'):
        if not self:
            with OrderCtx(field, direction).with_config(self.config) as lex:
                if lex:
                    self.field = lex

    def lex(self):
        if self:
            return self._template.format(field=self.field)
        return ''


class LimitNode(ConfigMixin):
    _template = 'LIMIT {offset},{limit}'

    def __init__(self):
        super(LimitNode, self).__init__()
        self.offset = None
        self.limit = None

    def __bool__(self):
        return self.offset is not None and self.limit is not None

    def set_range(self, offset, limit):
        if not self:
            with LimitCtx(offset, limit).with_config(self.config) as pair:
                self.offset, self.limit = pair

    def lex(self):
        if self:
            return self._template.format(
                offset=self.offset,
                limit=self.limit
            )
        return ''


class OptionsContainer(ConfigMixin):
    _joiner = ', '
    _template = 'OPTION {options}'

    def __init__(self):
        super(OptionsContainer, self).__init__()
        self.options = deque([])

    def __bool__(self):
        return bool(self.options)

    def set_options(self, **kwargs):
        for option, params in kwargs.items():
            with OptionsCtx(option, params).with_config(self.config) as lex:
                if lex:
                    self.options.append(lex)

    def add_ranker(self, ranker):
        with OptionsCtx(
            'ranker', ranker
        ).with_config(self.config) as lex:
            if lex:
                self.options.append(lex)

    def add_max_matches(self, max_matches):
        with OptionsCtx(
            'max_matches', max_matches
        ).with_config(self.config) as lex:
            if lex:
                self.options.append(lex)

    def add_cutoff(self, cutoff):
        with OptionsCtx(
            'cutoff', cutoff
        ).with_config(self.config) as lex:
            if lex:
                self.options.append(lex)

    def add_max_query_time(self, max_query_time):
        with OptionsCtx(
            'max_query_time', max_query_time
        ).with_config(self.config) as lex:
            if lex:
                self.options.append(lex)

    def add_retry_count(self, retry_count):
        with OptionsCtx(
            'retry_count', retry_count
        ).with_config(self.config) as lex:
            if lex:
                self.options.append(lex)

    def add_retry_delay(self, retry_delay):
        with OptionsCtx(
            'retry_delay', retry_delay
        ).with_config(self.config) as lex:
            if lex:
                self.options.append(lex)

    def add_field_weights(self, **kwargs):
        with OptionsCtx(
            'field_weights', kwargs
        ).with_config(self.config) as lex:
            if lex:
                self.options.append(lex)

    def add_index_weights(self, **kwargs):
        with OptionsCtx(
            'index_weights', kwargs
        ).with_config(self.config) as lex:
            if lex:
                self.options.append(lex)

    def add_reverse_scan(self, is_reverse=True):
        with OptionsCtx(
            'reverse_scan', is_reverse
        ).with_config(self.config) as lex:
            if lex:
                self.options.append(lex)

    def add_comment(self, comment):
        with OptionsCtx(
            'comment', comment
        ).with_config(self.config) as lex:
            if lex:
                self.options.append(lex)

    def lex(self):
        if self:
            return self._template.format(
                options=self._joiner.join(self.options)
            )
        return ''


class UpdateSetNode(ConfigMixin):
    _template = 'UPDATE {indexes} SET {values}'
    _joiner = ', '

    def __init__(self, indexes=None):
        super(UpdateSetNode, self).__init__()
        self.indexes = indexes
        self.set_values = set()

    def update(self, field, value):
        with UpdateSetCtx(field, value).with_config(self.config) as lex:
            self.set_values.add(lex)

    def lex(self):
        if self.set_values:
            return self._template.format(
                indexes=self._joiner.join(self.indexes),
                values=self._joiner.join(self.set_values)
            )
        return ''


class OR(ConfigMixin):
    _wrapper = '(%s)'
    _joiner = ' OR '

    def __init__(self, **kwargs):
        super(OR, self).__init__()
        self.raw_attrs = kwargs
        self.children = []
        self.joiner = None

    def __join(self, or_inst, joiner):
        or_ = OR()
        or_.children.extend([self, or_inst])
        or_.joiner = joiner
        return or_

    def __or__(self, other):
        return self.__join(other, joiner=' OR ')

    def __and__(self, other):
        return self.__join(other, joiner=' AND ')

    def lex(self):
        flat_conditions = []
        flat_joiners = []

        def expand_tree(self):
            if self.joiner is not None:
                flat_joiners.append(self.joiner)
            if self.raw_attrs:
                cleaned_conditions = []
                for k_attr, v_attr in self.raw_attrs.items():
                    with ORFilterCtx(k_attr, v_attr).with_config(self.config) as lex:
                        if lex:
                            cleaned_conditions.append(lex)
                if cleaned_conditions:
                    flat_conditions.append(
                        self._wrapper % self._joiner.join(cleaned_conditions)
                    )
            for c in self.children:
                expand_tree(
                    c.with_config(self.config)
                    if not c.has_config()
                    else c
                )
            flat_joiners.reverse()
            return flat_conditions, flat_joiners

        flat_conditions, flat_joiners = expand_tree(self)
        joiners = iter(flat_joiners)
        lex = reduce(
            lambda x, y: next(joiners).join([x, y]),
            flat_conditions
        )
        return lex


class AggregateObject(ConfigMixin):
    _agg_template = None
    _alias_template = None

    def __init__(self, field=None, alias=None):
        super(AggregateObject, self).__init__()
        if self._agg_template is None or self._alias_template is None:
            raise NotImplementedError(
                'Im am AggregateObject base class, '
                'inherit me and implement what you need'
            )

        self.raw_attrs = (field, alias or self._alias_template.format(field=field))

    def lex(self):
        raw_field, raw_alias = self.raw_attrs
        with AliasFieldCtx(
            raw_field, raw_alias
        ).called_by(
            self.__class__
        ).with_config(
            self.config
        ) as lex:
            return '' if not lex else self._agg_template.format(
                field=raw_field,
                alias=raw_alias,
            )


class RawAttr(ConfigMixin):
    _template = '{field} AS {alias}'

    def __init__(self, field, alias):
        self.field = field
        self.alias = alias

    def lex(self):
        with AliasFieldCtx(
            self.field, self.alias
        ).called_by(
            self.__class__
        ).with_config(
            self.config
        ) as lex:
            return '' if not lex else self._template.format(
                field=self.field,
                alias=self.alias
            )
        return


class Avg(AggregateObject):
    _agg_template = 'AVG({field}) AS {alias}'
    _alias_template = '{field}_avg'


class Min(AggregateObject):
    _agg_template = 'MIN({field}) AS {alias}'
    _alias_template = '{field}_min'


class Max(AggregateObject):
    _agg_template = 'MAX({field}) AS {alias}'
    _alias_template = '{field}_max'


class Sum(AggregateObject):
    _agg_template = 'SUM({field}) AS {alias}'
    _alias_template = '{field}_sum'


class Count(AggregateObject):
    _agg_template = 'COUNT(DISTINCT {field}) AS {alias}'
    _star_agg_template = 'COUNT({field}) AS {alias}'
    _alias_template = '{field}_count'

    def __init__(self, field='*', alias='num'):
        super(Count, self).__init__(field, alias)

    def lex(self):
        raw_field, raw_alias = self.raw_attrs
        with AliasFieldCtx(
            raw_field, raw_alias
        ).called_by(
            self.__class__
        ).with_config(
            self.config
        ) as lex:
            if raw_field == '*':
                template = self._star_agg_template
            else:
                template = self._agg_template
                if raw_alias == 'num':
                    raw_alias = self._alias_template.format(field=raw_field)

            return '' if not lex else template.format(field=raw_field, alias=raw_alias)


class SnippetsOptionsContainer(ConfigMixin):
    _joiner = ', '

    def __init__(self):
        super(SnippetsOptionsContainer, self).__init__()
        self.options = []

    def __bool__(self):
        return bool(self.options)

    def set_options(self, **kwargs):
        for option, params in kwargs.items():
            with SnippetsOptionsCtx(option, params).with_config(self.config) as lex:
                if lex and lex not in self.options:
                    self.options.append(lex)

    def lex(self):
        if self:
            return self._joiner.join(self.options)
        return ''


class SnippetsQueryNode(ConfigMixin):
    _joiner = ', '
    _template = "{data}, '{index}', '{query}'"

    def __init__(self, index=None):
        super(SnippetsQueryNode, self).__init__()
        self.index = index
        self.data = []
        self.query = []

    def __bool__(self):
        return all((self.index, self.data, self.query))

    def add_data(self, *data):
        data = sparse_free_sequence(data)
        for value in data:
            value = string_from_string(value, self.is_strict)
            if value and value not in self.data:
                self.data.append(value)
        return self

    def add_query(self, query):
        with MatchQueryCtx(query).with_config(self.config) as lex:
            if lex and lex not in self.query:
                self.query.append(lex)
        return self

    def lex(self):
        if not self:
            return ''

        if len(self.data) == 1:
            data_wrapper = "{data}"
        else:
            data_wrapper = "({data})"

        data = data_wrapper.format(
            data=self._joiner.join(["'%s'" % d for d in self.data])
        )

        return self._template.format(
            data=data,
            index=self.index,
            query=' '.join(self.query)
        )
