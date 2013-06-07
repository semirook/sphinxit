"""
    sphinxit.search
    ~~~~~~~~~~~~~~~

    Implements convertors and cleaners processors.

    :copyright: (c) 2013 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import unicode_literals

import re
import six
from datetime import datetime, date

from sphinxit.core.constants import ESCAPED_CHARS, RESERVED_KEYWORDS
from sphinxit.core.exceptions import SphinxQLSyntaxException
from sphinxit.core.helpers import (
    list_of_integers_only,
    int_from_digit,
    unix_timestamp
)
from sphinxit.core.mixins import CtxMixin


class FilterCtx(CtxMixin):
    _allowed_conditions_map = {
        '__eq': '{a}={v}',
        '__neq': '{a}!={v}',
        '__gt': '{a}>{v}',
        '__gte': '{a}>={v}',
        '__lt': '{a}<{v}',
        '__lte': '{a}<={v}',
        '__in': '{a} IN ({v})',
        '__between': '{a} BETWEEN {f_v} AND {s_v}',
    }

    def __init__(self, k_attr, v_attr):
        super(FilterCtx, self).__init__()
        self.k_attr = k_attr
        self.v_attr = v_attr

    def __enter__(self):
        v_attr = self.v_attr
        if isinstance(v_attr, six.string_types):
            v_attr = int_from_digit(
                v_attr,
                is_strict=self.is_strict
            )
        if isinstance(self.v_attr, (tuple, list)):
            v_attr = list_of_integers_only(
                v_attr,
                is_strict=self.is_strict
            )
        if isinstance(self.v_attr, (datetime, date)):
            v_attr = unix_timestamp(self.v_attr)

        if not v_attr and v_attr != 0:
            return None

        for ending in self._allowed_conditions_map.keys():
            if not self.k_attr.endswith(ending):
                continue

            if (
                ending not in ('__between', '__in')
                and isinstance(v_attr, (tuple, list))
                and not self.__exit__(
                    exc_val=SphinxQLSyntaxException(
                        '%s found but not allowed for %s condition' %
                        (self.v_attr, self.k_attr)
                    )
                )
            ):
                continue

            if (
                ending in ('__between', '__in')
                and not isinstance(v_attr, (tuple, list))
                and not self.__exit__(
                    exc_val=SphinxQLSyntaxException(
                        '%s condition found but the type of %s is not list or tuple' %
                        (self.k_attr, self.v_attr)
                    )
                )
            ):
                continue

            a = self.k_attr[:self.k_attr.rindex(ending)]
            v = v_attr

            if ending == '__between':
                if (
                    (len(v_attr) != 2 or len(v_attr) != len(self.v_attr))
                    and not self.__exit__(
                        exc_val=SphinxQLSyntaxException(
                            '%s condition wants a pair value and %s is not' %
                            (self.k_attr, self.v_attr)
                        )
                    )
                ):
                    continue

                f_v, s_v = v_attr
                return self._allowed_conditions_map[ending].format(
                    a=a,
                    f_v=f_v,
                    s_v=s_v
                )

            if ending == '__in':
                v = ','.join([str(v) for v in v_attr])

            return self._allowed_conditions_map[ending].format(a=a, v=v)

        return self.__exit__(
            exc_val=SphinxQLSyntaxException(
                '%s is invalid condition' % self.k_attr
            )
        )


class ORFilterCtx(FilterCtx):
    _allowed_conditions_map = {
        '__eq': '{a}={v}',
        '__gt': '{a}>{v}',
        '__gte': '{a}>={v}',
        '__lt': '{a}<{v}',
        '__lte': '{a}<={v}',
    }


class MatchQueryCtx(CtxMixin):

    def __init__(self, query, raw=False):
        super(MatchQueryCtx, self).__init__()
        self.query = query
        self.is_raw = raw

    def __enter__(self):
        if not isinstance(self.query, six.string_types):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" query is not a string' % self.query
                )
            )
        if not bool(self.query.strip()):
            return None

        if not self.is_raw:
            single_escape_chars_re = '|\\'.join(ESCAPED_CHARS.single_escape)
            self.query = re.sub(
                single_escape_chars_re,
                lambda m: r'\%s' % m.group(),
                self.query
            )
            double_escape_chars_re = '|\\'.join(ESCAPED_CHARS.double_escape)
            self.query = re.sub(
                double_escape_chars_re,
                lambda m: r'\\%s' % m.group(),
                self.query
            )

        return self.query


class FieldCtx(CtxMixin):

    def __init__(self, field):
        super(FieldCtx, self).__init__()
        self.field = field

    def __enter__(self):
        if not isinstance(self.field, six.string_types):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" is not a string' % self.field
                )
            )
        if self.field.upper() in RESERVED_KEYWORDS:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" is reserved keyword for Sphinx' % self.field
                )
            )
        if not bool(self.field.strip()):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException('The field is empty')
            )

        return self.field


class AliasFieldCtx(CtxMixin):

    def __init__(self, field, alias):
        super(AliasFieldCtx, self).__init__()
        self.field = field
        self.alias = alias
        self.called_cls = None

    def called_by(self, cls):
        self.called_cls = cls
        return self

    def __enter__(self):
        error_prefix = (
            'Trouble with %s. ' % self.called_cls.__name__
            if self.called_cls else ''
        )
        if not isinstance(self.field, six.string_types):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    error_prefix + '"%s" field is not a string' % self.field
                )
            )
        if not isinstance(self.alias, six.string_types):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" alias is not a string' % self.field
                )
            )
        if self.alias.upper() in RESERVED_KEYWORDS:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" is reserved keyword for Sphinx' % self.alias
                )
            )
        if self.field.upper() in RESERVED_KEYWORDS:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" is reserved keyword for Sphinx' % self.field
                )
            )
        if not bool(self.field.strip()):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException('The field is empty')
            )
        if not bool(self.alias.strip()):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException('The alias is empty')
            )

        return '%s AS %s' % (self.field, self.alias)


class OrderCtx(CtxMixin):

    def __init__(self, field, direction):
        super(OrderCtx, self).__init__()
        self.field = field
        self.direction = direction

    def __enter__(self):
        if not isinstance(self.field, six.string_types):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" field is not a string' % self.field
                )
            )
        if self.field.upper() in RESERVED_KEYWORDS:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" field is reserved keyword in Sphinx '
                    'and invalid for field name' % self.field
                )
            )
        if not bool(self.field.strip()):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException('The field is empty')
            )
        if (
            not isinstance(self.direction, six.string_types)
            or self.direction.upper() not in ('ASC', 'DESC')
        ):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    'Order direction can be ASC or DESC, "%s" is not' % self.direction
                )
            )

        return '%s %s' % (self.field, self.direction.upper())


class LimitCtx(CtxMixin):

    def __init__(self, offset, limit):
        super(LimitCtx, self).__init__()
        self.offset = offset
        self.limit = limit

    def __enter__(self):
        pair = list_of_integers_only(
            [self.offset, self.limit],
            is_strict=self.is_strict,
        )
        if len(pair) != 2:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    'LIMIT clause wants a pair value and %s is not' % pair
                )
            )

        offset, limit = pair
        if offset < 0:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '%s offset is less then 0' % offset
                )
            )
        if limit <= 0:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    'The limit value has to be greater then 0, %s is not' % limit
                )
            )

        return pair


class OptionsCtx(CtxMixin):

    def __init__(self, option, params):
        super(OptionsCtx, self).__init__()
        self.option = option
        self.params = params

    def __enter__(self):
        options_list = (
            'ranker',
            'max_matches',
            'cutoff',
            'max_query_time',
            'retry_count',
            'retry_delay',
            'field_weights',
            'index_weights',
            'reverse_scan',
            'comment',
        )
        if self.option in options_list:
            return getattr(self, 'get_%s' % self.option)()
        else:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '%s is unknown option' % self.option
                )
            )

    def get_ranker(self):
        ranker = self.params
        valid_rankers = (
            'proximity_bm25',
            'bm25',
            'none',
            'wordcount',
            'proximity',
            'matchany',
            'fieldmask',
        )
        if not ranker in valid_rankers:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '%s is unknown ranker. '
                    'Valid values are %s' % (
                        ranker,
                        ', '.join(['"%s"' % r for r in valid_rankers])
                    )
                )
            )

        return 'ranker=%s' % ranker

    def get_max_matches(self):
        value = int_from_digit(self.params, is_strict=self.is_strict)
        if not value:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException('"max_matches" option is empty')
            )
        return 'max_matches=%s' % value

    def get_cutoff(self):
        value = int_from_digit(self.params, is_strict=self.is_strict)
        if not value:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException('"cutoff" option is empty')
            )
        return 'cutoff=%s' % value

    def get_max_query_time(self):
        value = int_from_digit(self.params, is_strict=self.is_strict)
        if not value:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException('"max_query_time" option is empty')
            )
        return 'max_query_time=%s' % value

    def get_retry_count(self):
        value = int_from_digit(self.params, is_strict=self.is_strict)
        if not value:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException('"retry_count" option is empty')
            )
        return 'retry_count=%s' % value

    def get_retry_delay(self):
        value = int_from_digit(self.params, is_strict=self.is_strict)
        if not value:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException('"retry_delay" option is empty')
            )
        return 'retry_delay=%s' % value

    def get_field_weights(self):
        if not isinstance(self.params, dict):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '%s is not a dict as expected' % str(self.params)
                )
            )

        clean_pairs = []
        for field, value in self.params.items():
            if not isinstance(field, six.string_types):
                return self.__exit__(
                    exc_val=SphinxQLSyntaxException(
                        '%s is not a string as expected' % field
                    )
                )
            value = int_from_digit(value, is_strict=self.is_strict)
            if not value:
                if not self.__exit__(
                    exc_val=SphinxQLSyntaxException(
                        'One of the "field_weights" is not valid integer value'
                    )
                ):
                    continue
            else:
                clean_pairs.append('='.join([field, str(value)]))

        return 'field_weights=(%s)' % ', '.join(clean_pairs)

    def get_index_weights(self):
        if not isinstance(self.params, dict):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '%s is not a dict as expected' % str(self.params)
                )
            )

        clean_pairs = []
        for field, value in self.params.items():
            if not isinstance(field, six.string_types):
                return self.__exit__(
                    exc_val=SphinxQLSyntaxException(
                        '%s is not a string as expected' % field
                    )
                )
            value = int_from_digit(value, self.is_strict)
            if not value:
                if not self.__exit__(
                    exc_val=SphinxQLSyntaxException(
                        'One of the "index_weights" is not valid integer value'
                    )
                ):
                    continue
            else:
                clean_pairs.append('='.join([field, str(value)]))

        return 'index_weights=(%s)' % ', '.join(clean_pairs)

    def get_reverse_scan(self):
        if not isinstance(self.params, bool):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '%s has to be True or False' % self.params
                )
            )

        to_reverse = 1 if self.params else 0

        return 'reverse_scan=%s' % to_reverse

    def get_comment(self):
        if not isinstance(self.params, six.string_types):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '%s is not a string as expected' % self.params
                )
            )

        return 'comment=%s' % self.params


class UpdateSetCtx(CtxMixin):

    def __init__(self, k_attr, v_attr):
        super(UpdateSetCtx, self).__init__()
        self.k_attr = k_attr
        self.v_attr = v_attr

    def __enter__(self):
        if not isinstance(self.k_attr, six.string_types):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '%s is not a string as expected' % self.k_attr
                )
            )
        if not bool(self.k_attr.strip()):
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    'Field is empty'
                )
            )

        if isinstance(self.v_attr, (list, tuple)):
            v_attr = '(%s)' % ','.join([
                str(v) for v in list_of_integers_only(
                    self.v_attr,
                    self.is_strict,
                )
            ])
        elif (
            isinstance(self.v_attr, six.string_types)
            and self.v_attr.isdigit()
        ):
            v_attr = self.v_attr
        elif isinstance(self.v_attr, (six.integer_types, float)):
            v_attr = str(self.v_attr)
        elif (
            isinstance(self.v_attr, six.string_types)
            and not bool(self.v_attr.strip())
            or self.v_attr is None
        ):
            v_attr = '()'
        else:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '%s is improper value for UPDATE clause' % self.v_attr
                )
            )

        return '%s=%s' % (self.k_attr, v_attr)


class SnippetsOptionsCtx(CtxMixin):

    def __init__(self, option, params):
        super(SnippetsOptionsCtx, self).__init__()
        self.option = option
        self.params = params

    def __enter__(self):
        options_list = (
            'before_match',
            'after_match',
            'chunk_separator',
            'limit',
            'around',
            'exact_phrase',
            'use_boundaries',
            'weight_order',
            'query_mode',
            'force_all_words',
            'limit_passages',
            'limit_words',
            'start_passage_id',
            'load_files',
            'load_files_scattered',
            'html_strip_mode',
            'allow_empty',
            'passage_boundary',
            'emit_zones',
        )

        if self.option in options_list:
            return getattr(self, self.option)()
        else:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" is unknown option for the SNIPPET clause' % self.option
                )
            )

    def before_match(self):
        return "'%s' AS before_match" % self.params

    def after_match(self):
        return "'%s' AS after_match" % self.params

    def chunk_separator(self):
        return "'%s' AS chunk_separator" % self.params

    def limit(self):
        return "%s AS limit" % self.params

    def around(self):
        return "%s AS around" % self.params

    def exact_phrase(self):
        return "%s AS around" % self.params

    def use_boundaries(self):
        return "%s AS exact_phrase" % self.params

    def weight_order(self):
        return "%s AS weight_order" % self.params

    def query_mode(self):
        return "%s AS query_mode" % self.params

    def force_all_words(self):
        return "%s AS force_all_words" % self.params

    def limit_passages(self):
        return "%s AS limit_passages" % self.params

    def limit_words(self):
        return "%s AS limit_words" % self.params

    def start_passage_id(self):
        return "%s AS start_passage_id" % self.params

    def load_files(self):
        return "%s AS load_files" % self.params

    def load_files_scattered(self):
        return "%s AS load_files_scattered" % self.params

    def html_strip_mode(self):
        allowed_modes = ("none", "strip", "index", "retain")
        if self.params is None:
            self.params = "none"
        if self.params not in allowed_modes:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" is unknown strip mode' % self.params
                )
            )

        return "'%s' AS html_strip_mode" % self.params

    def allow_empty(self):
        return "%s AS allow_empty" % self.params

    def passage_boundary(self):
        allowed_modes = ("sentence", "paragraph", "zone")
        if self.params not in allowed_modes:
            return self.__exit__(
                exc_val=SphinxQLSyntaxException(
                    '"%s" is unknown boundary mode' % self.params
                )
            )

        return "'%s' AS passage_boundary" % self.params

    def emit_zones(self):
        return "%s AS emit_zones" % self.params
