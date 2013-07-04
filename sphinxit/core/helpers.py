"""
    sphinxit.core.helpers
    ~~~~~~~~~~~~~~~~~~~~~

    Implements useful set of helpers.

    :copyright: (c) 2013 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import unicode_literals

import time
import six

from sphinxit.core.exceptions import SphinxQLSyntaxException


def int_from_digit(value, is_strict=False):
    try:
        return int(value)
    except (ValueError, TypeError):
        if is_strict:
            raise SphinxQLSyntaxException('%s is not integer anyway' % value)
        else:
            return None


def string_from_string(value, is_strict=False):
    if not isinstance(value, six.string_types):
        if is_strict:
            raise SphinxQLSyntaxException('%s is not string anyway' % value)
        else:
            return None
    return value


def list_of_integers_only(sequence, is_strict=False):
    cleaned_sequence = []
    for orig_value in sequence:
        clean_value = int_from_digit(orig_value, is_strict)
        if clean_value is not None:
            cleaned_sequence.append(clean_value)
    return cleaned_sequence


def list_of_strings_only(sequence, is_strict=False):
    cleaned_sequence = []
    for orig_value in sequence:
        clean_value = string_from_string(orig_value, is_strict)
        if clean_value is not None:
            cleaned_sequence.append(clean_value)
    return cleaned_sequence


def sparse_free_sequence(sequence):
    return [
        x for x in sequence
        if (
            isinstance(x, six.string_types) and bool(x.strip())
            or not isinstance(x, six.string_types) and bool(x)
        )
    ]


def unix_timestamp(datetime):
    return str(int(time.mktime(datetime.timetuple())))


class BaseSearchConfig(object):
    DEBUG = True
    WITH_META = True
    WITH_STATUS = True
    POOL_SIZE = 5
    SEARCHD_CONNECTION = {
        'host': '127.0.0.1',
        'port': 9306,
    }
    # For future usage
    SNIPPETS_DEFAULTS = {
        'before_match': '<strong>',
        'after_match': '</strong>',
    }
