.. _changelog:

Changelog
=========

Version 0.3.1 (2013-07-05)
--------------------------

* Fixed OR objects workaround, more correct SphinxQL expression
* Updated connector with simple connection pool
* New ``POOL_SIZE`` config attribute
* :class:`BaseSearchConfig` in the ``sphinxit.core.helpers`` module
* Batch processing with subqueries (aka "facets"), updated :meth:`ask()` method.
* More tests and some optimizations

Version 0.3 (2013-06-07)
------------------------

* Completely rewritten library (from scratch, really)
* New master classes for queries - :class:`Search` and :class:`Snippet`
* New :meth:`ask()` method for query processing
* :class:`Q` object was renamed to :class:`OR` object, more meaningful name
* Explicit config class with ``DEBUG``, ``WITH_META``, ``WITH_STATUS`` and ``SEARCHD_CONNECTION`` attributes
* ``oursql`` and ``MySQLdb`` are both supported (``MySQLdb`` is the fallback)
* ``UPDATE`` syntax (for disk indexes only) is implemented
* ``OPTION`` clause is implemented
* Implicit arguments types corrections, if possible
* :class:``RawAttr`` object if you need more flexible queries
* Much more tests

Version 0.2.1 (2012-11-06)
--------------------------

* Python 2.6 compatibility is back
* ``unittest2`` usage fix for 2.6

Version 0.2 (2012-11-02)
--------------------------

* Python 3 compatibility (thanks to ``six`` layer)
* ``oursql`` as MySQL layer (no more ``MySQLdb``)
* Fixes in meta characters escaping
* The code is more polished and tested

Version 0.1.2 (2012-08-06)
--------------------------

* Connection on demand only (on the :meth:`process()` execution).
* Threaded connections and locks.

Version 0.1.1 (2012-07-31)
--------------------------

* Enhanced tests for lexemes.
* :class:`Q` objects should not work with ``!=``, ``IN`` and ``BETWEEN`` conditions (Sphinx restriction). Fixed.
* :class:`Sphinxit.Snippets` accepts single string as the :attr:`data` argument. Results single snippet string in such case.

Version 0.1 (2012-07-30)
------------------------
Released on July 30th 2012

First public release, ready for production.
