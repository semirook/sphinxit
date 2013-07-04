"""
    sphinxit.core.constants
    ~~~~~~~~~~~~~~~~~~~~~~~

    Defines some Sphinx-specific constants.

    :copyright: (c) 2013 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

from collections import namedtuple


RESERVED_KEYWORDS = (
    'AND',
    'AS',
    'ASC',
    'AVG',
    'BEGIN',
    'BETWEEN',
    'BY',
    'CALL',
    'COLLATION',
    'COMMIT',
    'COUNT',
    'DELETE',
    'DESC',
    'DESCRIBE',
    'DISTINCT',
    'FALSE',
    'FROM',
    'GLOBAL',
    'GROUP',
    'IN',
    'INSERT',
    'INTO',
    'LIMIT',
    'MATCH',
    'MAX',
    'META',
    'MIN',
    'NOT',
    'NULL',
    'OPTION',
    'OR',
    'ORDER',
    'REPLACE',
    'ROLLBACK',
    'SELECT',
    'SET',
    'SHOW',
    'START',
    'STATUS',
    'SUM',
    'TABLES',
    'TRANSACTION',
    'TRUE',
    'UPDATE',
    'VALUES',
    'VARIABLES',
    'WARNINGS',
    'WEIGHT',
    'WHERE',
    'WITHIN'
)


ESCAPED_CHARS = namedtuple('EscapedChars', ['single_escape', 'double_escape'])(
    single_escape=("'", '+', '[', ']', '=', '*'),
    double_escape=('@', '!', '^', '(', ')', '~', '-', '|', '/', '<<', '$', '"')
)

NODES_ORDER = namedtuple('NodesOrder', ['select', 'update'])(
    select=(
        'SelectFrom',
        'Where',
        'GroupBy',
        'OrderBy',
        'WithinGroupOrderBy',
        'Limit',
        'Options'
    ),
    update=(
        'UpdateSet',
        'Where',
        'Options'
    )
)
