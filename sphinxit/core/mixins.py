"""
    sphinxit.core.mixins
    ~~~~~~~~~~~~~~~~~~~~

    Implements mixins for nodes and processor.

    :copyright: (c) 2013 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import unicode_literals

from .exceptions import ImproperlyConfigured


class MagicMixin(object):

    def __bool__(self):
        return True

    def __nonzero__(self):
        return self.__bool__()

    def __str__(self):
        return self.lex()

    def lex(self):
        raise NotImplementedError("It's just mixin")


class ConfigMixin(MagicMixin):

    def __init__(self):
        self._config = None

    @property
    def config(self):
        if self._config is None:
            raise ImproperlyConfigured(
                'No config provided for instance processing'
            )
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    def with_config(self, config):
        self._config = config
        return self

    def has_config(self):
        return self._config is not None

    @property
    def is_strict(self):
        return getattr(self.config, 'DEBUG', False)


class CtxMixin(ConfigMixin):

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        if exc_val is not None and self.is_strict:
            raise exc_val
        return None
