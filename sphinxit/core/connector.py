from __future__ import unicode_literals

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


if not oursql and not mysqldb:
    raise ImproperlyConfigured(
        'Oursql or MySQLdb library has to be installed to work with MySQL protocol'
    )


class SphinxConnector(object):

    def __init__(self, config):
        default_options = {
            'host': '127.0.0.1',
            'port': 9306,
        }
        if isinstance(config, dict):
            default_options.update(config)
        elif (
            getattr(config, 'SEARCHD_CONNECTION', None)
            and isinstance(config.SEARCHD_CONNECTION, dict)
        ):
            default_options.update(config.SEARCHD_CONNECTION)

        self.options = default_options
        self.with_meta = getattr(config, 'WITH_META', False)
        self.with_status = getattr(config, 'WITH_STATUS', False)

    def get_connection(self):
        if oursql:
            try:
                return mysql_client.connect(**self.options)
            except Exception as e:
                if oursql and type(e).__name__ == 'ProgrammingError':
                    errno, msg, extra = e
                    raise SphinxQLDriverException(msg)
                raise SphinxQLDriverException(e)
        if mysqldb:
            try:
                return mysql_client.connect(
                    cursorclass=mysql_client.cursors.DictCursor,
                    use_unicode=self.options.pop('use_unicode', True),
                    charset=self.options.pop('charset', 'utf8'),
                    **self.options
                )
            except Exception as e:
                raise SphinxQLDriverException(e)

    def execute(self, sxql_query, no_extra=False):
        connection = self.get_connection()
        if oursql:
            curs = connection.cursor(mysql_client.DictCursor)
            execute_query = lambda sxql_query: curs.execute(sxql_query, plain_query=True)
        if mysqldb:
            curs = connection.cursor()
            execute_query = lambda sxql_query: curs.execute(sxql_query)

        normalize_meta = lambda result: dict([(x['Variable_name'], x['Value']) for x in result])

        total_results = {}
        try:
            execute_query(sxql_query)
            total_results['result'] = curs.fetchall()
            if self.with_meta and not no_extra:
                execute_query('SHOW META')
                total_results['meta'] = normalize_meta(curs.fetchall())
            if self.with_status and not no_extra:
                execute_query('SHOW STATUS')
                total_results['status'] = normalize_meta(curs.fetchall())
            return total_results
        except Exception as e:
            if oursql and type(e).__name__ == 'ProgrammingError':
                errno, msg, extra = e
                if errno is None:
                    return total_results  # empty result workaround
                raise SphinxQLDriverException(msg)
            raise SphinxQLDriverException(e)
        finally:
            curs.close()
