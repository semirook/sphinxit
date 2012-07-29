# -*- coding: utf-8 -*-

"""
    sphinxit.search
    ~~~~~~~~~~~~~~~

    Implements SphinxQL expression processing.

    :copyright: (c) 2012 by Roman Semirook.
    :license: BSD, see LICENSE for more details.
"""

import itertools
from exceptions import SphinxQLSyntaxException, SphinxQLChainException
from lexemes import (SXQLSelect, SXQLFrom, SXQLMatch, SXQLWhere, SXQLOrder, SXQLLimit, SXQLGroupBy,
                     SXQLWithinGroupOrderBy, SXQLFilter, SXQLORFilter, Count)


class LexContainer(object):
    """
    Container of the lexemes to accumulate calls for further SphinxQL expression assembly
    """
    def __init__(self):
        self.select_sx = SXQLSelect()
        self.from_sx = SXQLFrom()
        self.limit_sx = SXQLLimit()
        self.order_sx = SXQLOrder()
        self.group_by_sx = SXQLGroupBy()
        self.match_sx = SXQLMatch()
        self.where_sx = SXQLWhere()
        self.filters_sx = SXQLFilter()
        self.or_filters_sx = SXQLORFilter()
        self.within_group_order_by_sx = SXQLWithinGroupOrderBy()

        # It's the minimum set of lexemes to make valid SphinxQL query
        # SELECT * FROM some_index
        self.release_chain = set([self.select_sx, self.from_sx])


class SphinxBasicContainerMixin(object):
    """
    Initializes new query container for each new query
    """
    def __init__(self, *args):
        self._container = LexContainer()
        self._container.from_sx(*args)


class SphinxSearchActionMethods(SphinxBasicContainerMixin):
    """
    Implements SphinxQL `SELECT syntax <http://sphinxsearch.com/docs/current.html#sphinxql-select>`_.
    """

    def select(self, *args):
        """
        You can specify the list of attributes in results table::

            Sphinxit('index').select('id', 'title')

        .. code-block:: sql
            
            SELECT id, title FROM index

        if you don`t specify any attributes::

            Sphinxit('index')

        .. code-block:: sql

            SELECT * FROM index

        :param args: one or more Sphinx attributes names, separated with comma.
        """
        if args:
            self._container.select_sx(*args)

        return self

    def match(self, query=None, escape=True):
        """
        Match maps to fulltext query. By default it escapes user query to make
        it safe for ``searchd`` and it's just what you need in most cases::

            Sphinxit('index').match('semirook@gmail.com')

        .. code-block:: sql

            SELECT * FROM index WHERE MATCH('semirook\\@gmail.com')

        You can set :attr:`escape` attribute to ``False`` to use extended query syntax 
        (http://sphinxsearch.com/docs/current.html#extended-syntax) without escaping special symbols::

            Sphinxit('index').match('@email "semirook@gmail.com"', escape=False)

        .. code-block:: sql

            SELECT * FROM index WHERE MATCH('@email "semirook@gmail.com"')

        In some cases you may need to concatenate sub-queries (I had such case, really).
        Some trick makes that for you implicitly::

            Sphinxit('index').match('Hello').match('World!')

        .. code-block:: sql

            SELECT * FROM index WHERE MATCH('Hello World\\!')

        :param query: fulltext query.
        :param escape: switches query post-processing.
        """
        if query:
            self._container.match_sx(query, escape)
            self._container.where_sx(self._container.match_sx)
            self._container.release_chain.add(self._container.where_sx)

        return self

    def filter(self, *args, **kwargs):
        """
        Provides simple and clean interface for filtering search results within different 
        comparison operators like (=, !=, <, >, <=, >=), IN, BETWEEN and even OR (Sphinx doesn't support it yet).
        Sphinxit uses Django-style syntax for that.

        ==============================  ============================
        Sphinxit                        SphinxQL
        ==============================  ============================
        attr__eq = value                attr > value
        attr__neq = value               attr != value
        attr__gt = value                attr > value
        attr__gte = value               attr >= value
        attr__lt = value                attr < value
        attr__lte = value               attr <= value
        attr__in = [value, value]       attr IN (value, value)
        attr__between = [value, value]  attr BETWEEN value AND value
        ==============================  ============================

        The simplest example::

            Sphinxit('index').filter(id__gte=5)

        .. code-block:: sql

            SELECT * FROM index WHERE id>=5

        You can apply as much filters as you need by chaining :meth:`filter` methods.
        Note that these two queries are the same. Feel free::

            Sphinxit('index').filter(id__gte=5, counter__in=[1, 5])
            Sphinxit('index').filter(id__gte=5).filter(counter__in=[1, 5])

        .. code-block:: sql
            
            SELECT * FROM index WHERE id>=5 AND counter IN (1,5)

        Lyrical digression. I don't know why OR is not supported by Sphinx out of the box.
        It "will be in the future" but no one knows when. Sphinxit provides special Django-style
        ``Q`` syntax for that and makes some workaround::

            Sphinxit('index').filter(Q(id__eq=1, id__gte=5))

        .. code-block:: sql

            SELECT *, (id>=5 AND id=1) AS cnd FROM index WHERE cnd>0

        It works well even with more complex queries, you can mix Q and simple filters in one chain,
        add as much Q expressions as you want::

            Sphinxit('index').filter(Q(id__eq=1) | Q(id__gte=5)).filter(Q(counter__in=[1, 5]) & Q(id__lt=20)).filter(id__eq=2)

        .. code-block:: sql

            SELECT *, (id=1) OR (id>=5) AND (counter IN (1,5)) AND (id<20) AS cnd FROM index WHERE cnd>0 AND id=2

        You can specify more than one condition in atomic Q::

            Sphinxit('index').filter(Q(id__eq=1, id__gte=5) & Q(counter__eq=1, counter__gte=100))
        
        .. code-block:: sql

            SELECT *, (id=1 AND id>=5) AND (counter=1 AND counter>=100) AS cnd FROM index WHERE cnd>0

        You can use OR concatenation inside the pairs, just negate Q with ~::

            Sphinxit('index').filter(~Q(id__eq=1, id__gte=5) & ~Q(counter__eq=1, counter__gte=100))

        .. code-block:: sql

            SELECT *, (id=1 OR id>=5) AND (counter=1 OR counter>=100) AS cnd FROM index WHERE cnd>0

        :param args: one or more Q objects, separated with comma.
        :param kwargs: Sphinxit-specific filters, separated with comma.
        """
        if args or kwargs:
            if args:  # args are Q-objects
                self._container.or_filters_sx(*args)
                self._container.select_sx(self._container.or_filters_sx)
                self._container.where_sx(self._container.filters_sx(cnd__gt=0))  # simple hack for OR-filters
                self._container.release_chain.add(self._container.where_sx)
            if kwargs:  # kwargs are simple filter conditions
                self._container.filters_sx(**kwargs)
                self._container.where_sx(self._container.filters_sx)
                self._container.release_chain.add(self._container.where_sx)

        return self

    def order_by(self, *args):
        """
        You can order search results by any attribute with specified direction ('ASC' or 'DESC')::

            Sphinxit('index').order_by('title', 'asc')
        
        .. code-block:: sql

            SELECT * FROM index ORDER BY title ASC

        Ordering by several attributes is also possible::

            Sphinxit('index').order_by('title', 'asc').order_by('name', 'desc')

        .. code-block:: sql

            SELECT * FROM index ORDER BY title ASC, name DESC

        :param args: ordering Sphinx attribute name and direction ('ASC' or 'DESC').
        """
        if args:
            self._container.order_sx(*args)
            self._container.release_chain.add(self._container.order_sx)

        return self

    def group_by(self, *args):
        """
        Currently supports grouping just by a single attribute (Sphinx restriction)::

            Sphinxit('index').group_by('counter)

        .. code-block:: sql

            SELECT * FROM index GROUP BY counter

        :param args: grouping Sphinx attribute name.
        """
        if args:
            self._container.group_by_sx(*args)
            self._container.release_chain.add(self._container.group_by_sx)

        return self

    def within_group_order_by(self, *args):
        """
        This is a Sphinx specific extension that lets you control how
        the best row within a group will to be selected::

            Sphinxit('index').within_group_order_by('title', 'ASC')

        .. code-block:: sql

            SELECT * FROM index WITHIN GROUP ORDER BY title ASC

        :param args: grouping Sphinx attribute name and ordering direction ('ASC' or 'DESC').
        """
        if args:
            self._container.within_group_order_by_sx(*args)
            self._container.release_chain.add(self._container.within_group_order_by_sx)

        return self

    def limit(self, *args):
        """
        An implicit ``LIMIT 0,20`` is present in Sphinx by default.
        You can specify your own offset and limit values::

            Sphinxit('index').limit(20,1000)

        .. code-block:: sql

            SELECT * FROM index LIMIT 20,1000

        :param args: OFFSET and LIMIT integers.
        """
        if args:
            self._container.limit_sx(*args)
            self._container.release_chain.add(self._container.limit_sx)

        return self

    def cluster(self, attr=None, alias=None):
        """
        This method is just an alias for commonly used counted grouping::

            Sphinxit('index').cluster('title')

        .. code-block:: sql

            SELECT *, COUNT(*) AS num FROM index GROUP BY title

        You can write this query in more explicit way if you want to::

            Sphinxit('index').select(Count()).group_by('title')

        :param attr: grouping Sphinx attribute name.
        :param alias: alias of the new calculated field (optional, `num` by default).
        """
        if attr:
            self._container.select_sx(Count(alias=alias))
            self._container.group_by_sx(attr)
            self._container.release_chain.add(self._container.group_by_sx)

        return self


class SphinxSearchBase(SphinxSearchActionMethods):

    def _sxql_dragon(self, set_of_lexemes):
        """
        Looks like magic but it's not. Each lexeme object has certain join rules
        with another lexemes. Result container can contain several special SXQL objects
        and we need to concatenate them in the right order. Only one combination is proper.
        It works fast, really.
        """
        sxql_permutations = itertools.permutations(set_of_lexemes)
        bingo = None
        for sxql in sxql_permutations:
            try:
                reduce(lambda x, y: x + y, sxql)  # if we can do that, the combination is correct
                bingo = sxql
            except SphinxQLChainException:
                pass

        if bingo:
            return u' '.join([x.lex for x in bingo])  # this is our result SphinxQL expression
        else:
            raise SphinxQLSyntaxException('Cannot process correct SphinxQL expression')

    def get_sxql(self):
        """
        Call this method for debugging result SphinxQL query::

            Sphinxit('index').select('id', 'title').get_sxql()

        .. code-block:: sql
            
            SELECT id, title FROM index
        """
        return self._sxql_dragon(self._container.release_chain)
