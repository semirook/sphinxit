"""
    sphinxit.core.connector
    ~~~~~~~~~~~~~~~~~~~~~~~

    Implements Sphinxit <-> searchd interaction.

    :copyright: (c) 2013 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import unicode_literals

import threading
from collections import deque

from .mixins import ConfigMixin
from .exceptions import ImproperlyConfigured, SphinxQLDriverException

oursql = False
mysqldb = False

try:
    import oursql as mysql_client
    oursql = True
except ImportError:
    try:
        import MySQLdb as mysql_client
        import MySQLdb.cursors
        mysqldb = True
    except ImportError:
        pass


class SphinxConnector(ConfigMixin):

    def __init__(self, config):
        connection_options = {
            'host': '127.0.0.1',
            'port': 9306,
        }
        connection_options.update(config.SEARCHD_CONNECTION)

        self.config = config
        self.connection_options = connection_options

        self.__connections_pool = deque([])
        self.__local = threading.local()
        self.__conn_lock = threading.Lock()

    def __del__(self):
        self.close_connections()

    def close_connections(self):
        with self.__conn_lock:
            if hasattr(self.__local, 'conn'):
                del self.__local.conn
            for connection in self.__connections_pool:
                del connection

    def get_connection(self):
        if not oursql and not mysqldb:
            raise ImproperlyConfigured(
                'Oursql or MySQLdb library has to be installed to work with searchd'
            )
        if not self.__connections_pool:
            for i in range(getattr(self.config, 'POOL_SIZE', 10)):
                if oursql:
                    self.__connections_pool.append(mysql_client.connect(
                        **self.connection_options
                    ))
                if mysqldb:
                    self.__connections_pool.append(mysql_client.connect(
                        cursorclass=mysql_client.cursors.DictCursor,
                        use_unicode=self.connection_options.pop('use_unicode', True),
                        charset=self.connection_options.pop('charset', 'utf8'),
                        **self.connection_options
                    ))

        with self.__conn_lock:
            self.__local.conn = self.__connections_pool.pop()

        return self.__local.conn

    def get_cursor(self, connection):
        if oursql:
            curs = connection.cursor(mysql_client.DictCursor)
        if mysqldb:
            curs = connection.cursor()

        return curs

    def _get_cursor_exec(self, curs):
        if oursql:
            execute_query = lambda sxql_query: curs.execute(sxql_query, plain_query=True)
        if mysqldb:
            execute_query = lambda sxql_query: curs.execute(sxql_query)

        return execute_query

    def _normalize_meta(self, raw_result):
        return dict([(x['Variable_name'], x['Value']) for x in raw_result])

    def _execute_batch(self, cursor, sxql_batch):
        total_results = {}
        extra = []
        if getattr(self.config, 'WITH_META', False):
            extra.append(('SHOW META', 'meta'))
        if getattr(self.config, 'WITH_STATUS', False):
            extra.append(('SHOW STATUS', 'status'))

        cursor_exec = self._get_cursor_exec(cursor)

        for sub_ql_pair in sxql_batch:
            subresult = {}
            sub_ql, sub_alias = sub_ql_pair
            cursor_exec(sub_ql)
            subresult['items'] = [r for r in cursor]

            for sub_meta_pair in extra:
                meta_ql, meta_alias = sub_meta_pair
                cursor_exec(meta_ql)
                subresult[meta_alias] = self._normalize_meta(cursor)

            total_results[sub_alias] = subresult

        return total_results

    def _execute_query(self, cursor, sxql_query):
        cursor_exec = self._get_cursor_exec(cursor)
        cursor_exec(sxql_query)

        return cursor.fetchall()

    def execute(self, sxql_query):
        connection = self.get_connection()
        cursor = self.get_cursor(connection)
        try:
            if isinstance(sxql_query, (tuple, list)):
                total_results = self._execute_batch(cursor, sxql_query)
            else:
                total_results = self._execute_query(cursor, sxql_query)
        except Exception as e:
            if oursql and type(e).__name__ == 'ProgrammingError':
                errno, msg, extra = e
                raise SphinxQLDriverException(msg)
            raise SphinxQLDriverException(e)
        finally:
            cursor.close()
            self.__connections_pool.appendleft(connection)

        return total_results
