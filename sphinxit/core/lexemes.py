"""
    sphinxit.lexemes
    ~~~~~~~~~~~~~~~~

    Implements special Sphinxit lexemes objects.

    :copyright: (c) 2012 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import unicode_literals
from __future__ import absolute_import

import six
from six.moves import filter, map

import re
import collections
from .exceptions import SphinxQLChainException, SphinxQLSyntaxException


RESERVED_KEYWORDS = ('AND', 'AS', 'ASC', 'AVG', 'BEGIN', 'BETWEEN', 'BY', 'CALL', 'COLLATION', 'COMMIT',
                     'COUNT', 'DELETE', 'DESC', 'DESCRIBE', 'DISTINCT', 'FALSE', 'FROM', 'GLOBAL', 'GROUP', 'ID',
                     'IN', 'INSERT', 'INTO', 'LIMIT', 'MATCH', 'MAX', 'META', 'MIN', 'NOT', 'NULL', 'OPTION', 'OR',
                     'ORDER', 'REPLACE', 'ROLLBACK', 'SELECT', 'SET', 'SHOW', 'START', 'STATUS', 'SUM',
                     'TABLES', 'TRANSACTION', 'TRUE', 'UPDATE', 'VALUES', 'VARIABLES',
                     'WARNINGS', 'WEIGHT', 'WHERE', 'WITHIN')


class SXQLSelect(object):
    _validator_exception_msg = 'Attributes are not defined or defined improperly.'
    _lex_string = 'SELECT {attrs}'
    _joiner_string = ', '

    def __init__(self, init_attrs=None):
        init_attrs = init_attrs or ['*']
        self._attrs = []
        self._modificators = []
        self._attrs.append(*self._clean_attrs(*init_attrs))

    @property
    def lex(self):
        if self._modificators:
            self._attrs.extend([l.lex for l in self._modificators])

        if not self._attrs:
            raise SphinxQLSyntaxException(self._validator_exception_msg)

        return self._lex_string.format(attrs=self._joiner_string.join(self._attrs))

    def _clean_attrs(self, *attrs):
        if self._is_modificators(*attrs):
            return filter(lambda x: x not in self._modificators, attrs)
        if self._is_attributes(*attrs):
            return filter(lambda x: x not in self._attrs, attrs)

    def _is_modificators(self, *attrs):
        return all(map(lambda x: isinstance(x, (SXQLORFilter, Count, Avg)), attrs))

    def _is_attributes(self, *attrs):
        return all(map(lambda x: isinstance(x, six.string_types), attrs))

    def __call__(self, *attrs):
        if self._is_modificators(*attrs):
            self._modificators.extend(self._clean_attrs(*attrs))
        elif self._is_attributes(*attrs):
            self._attrs.extend(self._clean_attrs(*attrs))
            if '*' in self._attrs:
                self._attrs.remove('*')
        else:
            raise SphinxQLSyntaxException(self._validator_exception_msg)

        return self

    def __add__(self, other):
        if isinstance(other, SXQLFrom):
            return other
        raise SphinxQLChainException()


class SXQLFrom(object):
    _validator_exception_msg = 'Indexes are not defined or defined improperly.'
    _lex_string = 'FROM {indexes}'
    _joiner_string = ', '

    def __init__(self):
        self._attrs = []

    @property
    def lex(self):
        if not self._attrs:
            raise SphinxQLSyntaxException(self._validator_exception_msg)

        joined_attrs = self._joiner_string.join(self._attrs)

        return self._lex_string.format(indexes=joined_attrs)

    def _clean_attrs(self, attrs):
        if not attrs or not all(map(lambda x: isinstance(x, six.string_types), attrs)):
            raise SphinxQLSyntaxException(self._validator_exception_msg)

        return filter(lambda x: x not in self._attrs, attrs)

    def __call__(self, *attrs):
        self._attrs.extend(self._clean_attrs(attrs))
        return self

    def __add__(self, other):
        if isinstance(other, (SXQLWhere, SXQLGroupBy, SXQLOrder, SXQLWithinGroupOrderBy, SXQLLimit)):
            return other
        raise SphinxQLChainException()


class CommonSXQLWhereMixin(object):
    _not_correct_attr_msg = "'{0}' condition is not allowed here."
    _attr_value_is_string_msg = 'Attribute value cannot be a string anyway.'
    _not_iterable_values_msg = "Condition has to be an iterable object. '{0}' is not."
    _not_integer_values_msg = "Condition has to be a set of integers. '{0}' is not."
    _not_valid_range_msg = "Condition has to be a range of two integers. '{0}' is not."
    _attr_value_is_range_msg = 'Attribute value has to be an integer, not range.'

    allowed_conditions_map = {'__eq': '{a}={v}',
                              '__neq': '{a}!={v}',
                              '__gt': '{a}>{v}',
                              '__gte': '{a}>={v}',
                              '__lt': '{a}<{v}',
                              '__lte': '{a}<={v}',
                              '__in': '{a} IN ({v})',
                              '__between': '{a} BETWEEN {f_v} AND {s_v}',
                              }

    def _clean_rendered_attrs(self, k_attr, v_attr):
        if isinstance(v_attr, six.string_types):
            try:
                v_attr = int(v_attr)
            except ValueError:
                raise SphinxQLSyntaxException(self._attr_value_is_string_msg)

        if (isinstance(v_attr, collections.Iterable)
            and not all(map(lambda x: isinstance(x, six.integer_types), v_attr))):
            try:
                v_attr = map(int, v_attr)
            except ValueError:
                raise SphinxQLSyntaxException(self._not_integer_values_msg.format(v_attr))

        for ending in self.allowed_conditions_map.keys():
            if not k_attr.endswith(ending):
                continue

            if ending not in ('__between', '__in') and isinstance(v_attr, collections.Iterable):
                raise SphinxQLSyntaxException(self._attr_value_is_range_msg)

            if ending in ('__between', '__in'):
                if not isinstance(v_attr, collections.Iterable):
                    raise SphinxQLSyntaxException(self._not_iterable_values_msg.format(v_attr))

            a = k_attr[:k_attr.rindex(ending)]
            v = v_attr

            if ending == '__between':
                if len(v_attr) != 2:
                    raise SphinxQLSyntaxException(self._not_valid_range_msg.format(v_attr))
                f_v, s_v = v_attr
                return self.allowed_conditions_map[ending].format(a=a, f_v=f_v, s_v=s_v)

            elif ending == '__in':
                v = ','.join(map(str, v_attr))

            return self.allowed_conditions_map[ending].format(a=a, v=v)

        raise SphinxQLSyntaxException(self._not_correct_attr_msg.format(k_attr))


class SXQLMatch(object):
    _validator_exception_msg = "The query has to be a string. '{0}' is not."
    _empty_exception_msg = 'No query defined for full-text search.'
    _single_escape_chars = ["'", '+', '[', ']', '=', '*']
    _double_escape_chars = ['@', '!', '^', '(', ')', '~', '-', '|', '/', '<<', '$', '"']
    _lex_string = "MATCH('{query}')"
    _joiner_string = ' '

    def __init__(self):
        self._attrs = []

    @property
    def lex(self):
        if not self._attrs:
            raise SphinxQLSyntaxException(self._empty_exception_msg)
        lex = self._lex_string.format(query=self._joiner_string.join(self._attrs))
        return lex

    def __call__(self, query, escape=True):
        if not isinstance(query, six.string_types):
            raise SphinxQLSyntaxException(self._validator_exception_msg.format(query))

        if escape:
            single_escape_chars_re = '|\\'.join(self._single_escape_chars)
            query = re.sub(single_escape_chars_re, lambda m: r'\{0}'.format(m.group()), query)

            double_escape_chars_re = '|\\'.join(self._double_escape_chars)
            query = re.sub(double_escape_chars_re, lambda m: r'\\{0}'.format(m.group()), query)

        self._attrs.append(query)

        return self

    def __add__(self, other):
        if isinstance(other, (SXQLGroupBy, SXQLOrder, SXQLWithinGroupOrderBy, SXQLLimit)):
            return other
        raise SphinxQLChainException()


class SXQLLimit(object):
    _unique_exception_msg = 'Only one LIMIT clause is allowed in the query.'
    _validator_exception_msg = 'OFFSET and LIMIT values are not defined or defined improperly.'
    _lex_string = "LIMIT {offset},{limit}"

    def __init__(self, offset=None, limit=None):
        if offset and limit:
            self.offset, self.limit = self._clean_attrs((offset, limit))
        else:
            self.offset = 0
            self.limit = 100

        self._is_called_once = False

    @property
    def lex(self):
        lex = self._lex_string.format(offset=self.offset, limit=self.limit)
        return lex

    def _clean_attrs(self, attrs):
        if len(attrs) != 2:
            raise SphinxQLSyntaxException(self._validator_exception_msg)

        if not all(map(lambda x: isinstance(x, six.integer_types), attrs)):
            try:
                attrs = map(int, attrs)
            except ValueError:
                raise SphinxQLSyntaxException(self._validator_exception_msg)

        return attrs

    def __call__(self, *attrs):
        if self._is_called_once:
            raise SphinxQLSyntaxException(self._unique_exception_msg)
        self.offset, self.limit = self._clean_attrs(attrs)
        self._is_called_once = True

        return self

    def __add__(self, other):
        raise SphinxQLChainException()


class SXQLOrder(object):
    _attrs_validator_exception_msg = 'Attributes are not defined or defined improperly.'
    _direction_validator_exception_msg = 'Order direction can be ASC or DESC only.'
    _lex_string = 'ORDER BY {clauses}'
    _joiner_string = ', '

    def __init__(self):
        self._attrs = []

    @property
    def lex(self):
        lex = self._lex_string.format(clauses=self._joiner_string.join(self._attrs))
        return lex

    def _clean_attrs(self, attrs):
        if len(attrs) != 2:
            raise SphinxQLSyntaxException(self._attrs_validator_exception_msg)

        attr, direction = attrs
        if not all(map(lambda x: isinstance(x, six.string_types), (attr, direction))):
            raise SphinxQLSyntaxException(self._attrs_validator_exception_msg)
        if direction.upper() not in ['ASC', 'DESC']:
            raise SphinxQLSyntaxException(self._direction_validator_exception_msg)

        return attr, direction

    def __call__(self, *attrs):
        attr, direction = self._clean_attrs(attrs)
        self._attrs.append('{attr} {direction}'.format(attr=attr, direction=direction.upper()))
        return self

    def __add__(self, other):
        if isinstance(other, (SXQLWithinGroupOrderBy, SXQLLimit)):
            return other
        raise SphinxQLChainException()


class SXQLGroupBy(object):
    _unique_exception_msg = 'Only one GROUP BY clause is allowed in the query.'
    _attr_validator_exception_msg = "Attribute name has to be a string. {0} is not."
    _no_attr_validator_exception_msg = 'No attribute name defined.'
    _lex_string = 'GROUP BY {attr}'

    def __init__(self):
        self._attr = None
        self._is_called_once = False

    @property
    def lex(self):
        lex = self._lex_string.format(attr=self._attr)
        return lex

    def _clean_attr(self, attr):
        if not attr:
            raise SphinxQLSyntaxException(self._no_attr_validator_exception_msg)
        if len(attr) != 1:
            raise SphinxQLSyntaxException(self._unique_exception_msg)
        if not isinstance(attr[0], six.string_types):
            raise SphinxQLSyntaxException(self._attr_validator_exception_msg.format(attr[0]))

        return attr[0]

    def __call__(self, *attr):
        if self._is_called_once:
            raise SphinxQLSyntaxException(self._unique_exception_msg)

        self._attr = self._clean_attr(attr)
        self._is_called_once = True

        return self

    def __add__(self, other):
        if isinstance(other, (SXQLOrder, SXQLWithinGroupOrderBy, SXQLLimit)):
            return other
        raise SphinxQLChainException()


class SXQLWithinGroupOrderBy(SXQLOrder):
    _unique_exception_msg = 'Only one WITHIN GROUP ORDER BY clause is allowed in the query'
    _lex_string = 'WITHIN GROUP ORDER BY {clauses}'

    def __init__(self):
        self._is_called_once = False
        super(SXQLWithinGroupOrderBy, self).__init__()

    def __call__(self, *attrs):
        if self._is_called_once:
            raise SphinxQLSyntaxException(self._unique_exception_msg)
        self._is_called_once = True

        return super(SXQLWithinGroupOrderBy, self).__call__(*attrs)

    def __add__(self, other):
        if isinstance(other, SXQLLimit):
            return other
        raise SphinxQLChainException()


class SXQLWhere(object):
    _validator_exception_msg = 'WHERE clause is not defined.'
    _container_exception_msg = 'SXQLWhere container is for SXQLFilter and SXQLMatch instances only.'
    _lex_string = 'WHERE {clauses}'
    _joiner_string = ' AND '

    def __init__(self):
        self._attrs = []

    @property
    def lex(self):
        return self._lex_string.format(clauses=self._joiner_string.join([l.lex for l in self._attrs]))

    def _clean_attrs(self, attrs):
        if not attrs:
            raise SphinxQLSyntaxException(self._validator_exception_msg)

        if not all(map(lambda x: isinstance(x, (SXQLFilter, SXQLMatch)), attrs)):
            raise SphinxQLSyntaxException(self._container_exception_msg)

        return filter(lambda x: x not in self._attrs, attrs)

    def __call__(self, *attrs):
        self._attrs.extend(self._clean_attrs(attrs))
        return self

    def __add__(self, other):
        if isinstance(other, (SXQLGroupBy, SXQLOrder, SXQLWithinGroupOrderBy, SXQLLimit)):
            return other
        raise SphinxQLChainException()


class SXQLORFilter(object):
    _lex_string = '{clauses} AS cnd'
    _joiner_string = ' AND '

    def __init__(self):
        self._attrs = []

    def __call__(self, *args):
        for arg in args:
            if isinstance(arg, Q):
                self._attrs.append(arg._q_buffer or arg.lex)

        return self

    @property
    def lex(self):
        lex = self._lex_string.format(clauses=self._joiner_string.join(self._attrs))
        return lex


class SXQLFilter(CommonSXQLWhereMixin):
    _lex_string = '{clauses}'
    _joiner_string = ' AND '

    def __init__(self):
        self._attrs = set()

    def __call__(self, **kwargs):
        for k_attr, v_attr in kwargs.items():
            self._attrs.add(self._clean_rendered_attrs(k_attr, v_attr))
        return self

    @property
    def lex(self):
        lex = self._lex_string.format(clauses=self._joiner_string.join(self._attrs))
        return lex


class Q(CommonSXQLWhereMixin):
    _validator_exception_msg = 'Empty Q expression is not allowed.'
    _lex_string = '({clauses})'
    _and_joiner = ' AND '
    _or_joiner = ' OR '

    allowed_conditions_map = {'__eq': '{a}={v}',
                              '__gt': '{a}>{v}',
                              '__gte': '{a}>={v}',
                              '__lt': '{a}<{v}',
                              '__lte': '{a}<={v}',
                              }

    def __init__(self, **kwargs):
        self._attrs = []
        self._q_buffer = None
        self._joiner_string = self._and_joiner

        for k_attr, v_attr in kwargs.items():
            self._attrs.append(self._clean_rendered_attrs(k_attr, v_attr))

    def _pair_resolve(self, one, two):
        if one._q_buffer:
            join_pair = [one._q_buffer, two.lex]
        elif two._q_buffer:
            join_pair = [two._q_buffer, self.lex]
        else:
            join_pair = [one.lex, two.lex]

        return join_pair

    def __or__(self, other):
        other._q_buffer = self._or_joiner.join(self._pair_resolve(self, other))
        return other

    def __and__(self, other):
        other._q_buffer = self._and_joiner.join(self._pair_resolve(self, other))
        return other

    def __add__(self, other):
        return self.__and__(other)

    def __invert__(self):
        self._joiner_string = self._or_joiner
        return self

    @property
    def lex(self):
        if not self._attrs:
            raise SphinxQLSyntaxException(self._validator_exception_msg)

        return self._lex_string.format(clauses=self._joiner_string.join(self._attrs))


class AggregateObject(object):
    _lex_string = None
    _default_alias_string = None

    _attr_validator_exception_msg = "Attribute name has to be a string. '{0}' is not."
    _alias_validator_exception_msg = "Alias name has to be a string. '{0}' is not."
    _alias_forbidden_exception_msg = "Alias '{0}' is reserved word and is not allowed."

    def __init__(self, attr=None, alias=None):
        self._attr = attr
        self._alias = alias
        if False in (self._lex_string, self._default_alias_string):
            raise NotImplementedError('Can`t find some attributes')

    def _clean_attrs(self, attr, alias):
        if not isinstance(attr, six.string_types):
            raise SphinxQLSyntaxException(self._attr_validator_exception_msg.format(attr))

        alias = alias or self._default_alias_string.format(attr=attr)

        if not isinstance(alias, six.string_types):
            raise SphinxQLSyntaxException(self._alias_validator_exception_msg.format(alias))
        if alias.upper() in RESERVED_KEYWORDS:
            raise SphinxQLSyntaxException(self._alias_forbidden_exception_msg.format(alias))

        return attr, alias

    @property
    def lex(self):
        attr, alias = self._clean_attrs(self._attr, self._alias)
        lex = self._lex_string.format(attr=attr, alias=alias)
        return lex


class Avg(AggregateObject):
    _lex_string = 'AVG({attr}) AS {alias}'
    _default_alias_string = '{attr}_avg'


class Min(AggregateObject):
    _lex_string = 'MIN({attr}) AS {alias}'
    _default_alias_string = '{attr}_min'


class Max(AggregateObject):
    _lex_string = 'MAX({attr}) AS {alias}'
    _default_alias_string = '{attr}_max'


class Sum(AggregateObject):
    _lex_string = 'SUM({attr}) AS {alias}'
    _default_alias_string = '{attr}_sum'


class Count(AggregateObject):
    _attr_lex_string = 'COUNT(DISTINCT {attr}) AS {alias}'
    _star_lex_string = 'COUNT({attr}) AS {alias}'
    _default_alias_string = '{attr}_count'

    @property
    def _lex_string(self):
        return self._attr_lex_string if self._attr else self._star_lex_string

    def _clean_attrs(self, attr, alias):
        if attr and not alias:
            alias = self._default_alias_string.format(attr=attr)
        elif not attr and not alias:
            alias = 'num'
        attr = attr or '*'

        return super(Count, self)._clean_attrs(attr, alias)


class SXQLSnippets(object):
    _default_lex_string = "CALL SNIPPETS(({data}), '{index}', '{query}')"
    _option_lex_string = "CALL SNIPPETS(({data}), '{index}', '{query}', {options})"
    _joiner_string = ', '

    _type_validator_exception_msg = "Wrong value for '{0}' snippet parameter is used. RTFM, please."
    _value_validator_exception_msg = "Wrong value for '{0}' snippet parameter is used. Allowed values are {1}."
    _parameter_validator_exception_msg = "'{0}' snippet parameter is not supported by Sphinx."
    _not_string_validator_exception_msg = "'{0}' attribute has to be a string."
    _data_validator_exception_msg = "Source data has to be a string or a list of strings. '{0} is not.'"

    excerpts_params = {"before_match": {'type': six.string_types, 'defaults': '<b>'},
                       "after_match": {'type': six.string_types, 'defaults': '</b>'},
                       "chunk_separator": {'type': six.string_types, 'defaults': '...'},
                       "limit": {'type': six.integer_types, 'defaults': 256},
                       "around": {'type': six.integer_types, 'defaults': 5},
                       "exact_phrase": {'type': bool, 'defaults': 0},
                       "single_passage": {'type': bool, 'defaults': 0},
                       "use_boundaries": {'type': bool, 'defaults': 0},
                       "weight_order": {'type': bool, 'defaults': 0},
                       "query_mode": {'type': bool, 'defaults': 0},
                       "force_all_words": {'type': bool, 'defaults': 0},
                       "limit_passages": {'type': bool, 'defaults': 0},
                       "limit_words": {'type': bool, 'defaults': 0},
                       "start_passage_id": {'type': six.integer_types, 'defaults': 1},
                       "load_files": {'type': bool, 'defaults': 0},
                       "load_files_scattered": {'type': bool, 'defaults': 0},
                       "html_strip_mode": {'type': six.string_types,
                                           'defaults': 'index',
                                           'allowed': ("none", "strip", "index", "retain")},
                       "allow_empty": {'type': bool, 'defaults': 0},
                       "passage_boundary": {'type': six.string_types,
                                            'defaults': 'sentence',
                                            'allowed': ("sentence", "paragraph", "zone")},
                       "emit_zones": {'type': bool, 'defaults': 0},
                       }

    type_to_str_map = {six.string_types: "'{0}' AS {1}",
                       six.integer_types: "{0} AS {1}",
                       bool: "{0} AS {1}",
                       }

    def __init__(self, index, data, query, options=None):
        self._data = data
        self._index = index
        self._query = query
        self._options = options or {}

    @property
    def _lex_string(self):
        return self._option_lex_string if self._options else self._default_lex_string

    def _clean_attr(self, attr):
        if not isinstance(attr, six.string_types):
            raise SphinxQLSyntaxException(self._not_string_validator_exception_msg.format(attr))

        attr = re.sub("'", lambda m: r'\{0}'.format(m.group()), attr)

        return attr

    def _clean_data(self, data):
        if not isinstance(data, collections.Iterable):
            raise SphinxQLSyntaxException(self._data_validator_exception_msg.format(data))
        if (not isinstance(data, six.string_types)
            and False in map(lambda d: isinstance(d, six.string_types), data)):
            raise SphinxQLSyntaxException(self._data_validator_exception_msg.format(data))
        if isinstance(data, six.string_types):
            data = [data]

        return map(lambda d: re.sub("'", lambda c: r'\{0}'.format(c.group()), d), data)

    def _clean_options(self, options):
        params_chain = []
        for k, v in options.items():
            if k not in self.excerpts_params.keys():
                raise SphinxQLSyntaxException(self._parameter_validator_exception_msg.format(k))

            param_info = self.excerpts_params[k]
            if not isinstance(v, param_info['type']):
                raise SphinxQLSyntaxException(self._type_validator_exception_msg.format(k))

            if param_info.get('allowed', False) and v not in param_info['allowed']:
                raise SphinxQLSyntaxException(
                    self._value_validator_exception_msg.format(
                        k, self._joiner_string.join(["'{0}'".format(s) for s in param_info['allowed']]),
                    )
                )
            if isinstance(v, bool):
                v = 1 if v else 0

            param_string = self.type_to_str_map[param_info['type']]
            params_chain.append(param_string.format(v, k))

        return self._joiner_string.join(params_chain)

    @property
    def lex(self):
        data = self._joiner_string.join(["'{0}'".format(s) for s in self._clean_data(self._data)])
        index = self._clean_attr(self._index)
        query = self._clean_attr(self._query)

        if self._options:
            lex = self._option_lex_string.format(
                data=data,
                index=index,
                query=query,
                options=self._clean_options(self._options))
        else:
            lex = self._default_lex_string.format(
                data=data,
                index=index,
                query=query)

        return lex
