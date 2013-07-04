.. _preparation:

Preparation
===========

You may have no experience with Sphinx config and that's ok. Sphinx has 
`great docs <http://sphinxsearch.com/docs/>`_ about configuration and tuning, 
and you can use wide range of special attributes to setup your own Sphinx instance.

To use something in further examples, here is my simple but full ``sphinx.conf`` that you can
adapt and use in your own projects as a config base. You don't have to understand all of this stuff
right now to start Searching. But Sphinx docs are your best friends, remember that.

.. code-block:: sql

    #############################################################################
    ## data source definition
    #############################################################################

    source common
    {
        type = pgsql
        sql_host = 127.0.0.1
        sql_user = postgres
        sql_pass = postgres
        sql_db = megaproject
    }

    source company: common
    {
        sql_query_range = SELECT MIN(id), MAX(id) FROM company
        sql_range_step = 10000
        sql_query =\
            SELECT company.id, \
                   company.name, \
                   company.date_created, \
                   "user".email AS owner_email \
            FROM company \
            LEFT JOIN "user" ON company.owner_id = "user".id \
            WHERE company.id BETWEEN $start AND $end

        sql_field_string = name
        sql_field_string = owner_email
        sql_attr_timestamp = date_created

        sql_attr_multi = uint products from ranged-query; \
            SELECT company_id, id FROM product \
            WHERE id >= $start AND id <= $end; \
            SELECT MIN(id), MAX(id) FROM product
    }

    #############################################################################
    ## index definition
    #############################################################################

    index common
    {
        type = plain
        docinfo = extern
        morphology = stem_en, stem_ru
        min_stemming_len = 2
        min_word_len = 2
        charset_type = utf-8
        html_strip = 1
        html_remove_elements = script
        html_index_attrs = img=alt,title; a=title;
        enable_star = 1

        charset_table = 0..9, A..Z->a..z, _, a..z, \
                        U+27, U+0401->U+0435, U+0451->U+0435, \
                        U+410..U+42F->U+430..U+44F, U+430..U+44F
    }

    index company: common
    {
        source = company
        path = /home/user/projects/megaproject/indexes
    }


    #############################################################################
    ## indexer settings
    #############################################################################

    indexer
    {
        mem_limit = 512M
        max_iosize = 524288
    }


    #############################################################################
    ## searchd settings
    #############################################################################

    searchd
    {
        listen = 9306:mysql41

        log = /home/user/projects/megaproject/logs/searchd.log
        query_log = /home/user/projects/megaproject/logs/query.log
        pid_file = /home/user/projects/megaproject/searchd.pid

        read_timeout = 5
        max_children = 30
        max_matches = 1000
        seamless_rotate = 1
        preopen_indexes = 0
        unlink_old = 1
        compat_sphinxql_magics = 0
    }

That's it! Really simple example. We've defined one index - ``company`` and four fields 
(attributes) we can use for filtering, ordering, grouping, etc.: 
``name`` (string), ``owner_email`` (string), ``date_created`` (timestamp) and ``products`` (MVA).

Use this config to create index files with ``indexer``::
    
    $ indexer -c /path/to/sphinx.conf --all

or to update already created indexes (rotation)::

    $ indexer -c /path/to/sphinx.conf --all --rotate

and run ``searchd`` daemon you will work with to make queries::

    $ searchd -c /path/to/sphinx.conf

SphinxQL works via it's own MySQL protocol implementation. That means that you can connect to the
``searchd`` with any mysql client! Cool and useful feature::

    $ mysql -h 0 -P 9306

Check your indexes definition by making some query, like this::

    mysql> select id from company order by date_created desc limit 10;
    +--------+
    | id     |
    +--------+
    | 869656 |
    | 869657 |
    | 869658 |
    | 869659 |
    | 869660 |
    | 869661 |
    | 869662 |
    | 869663 |
    | 869664 |
    | 869665 |
    +--------+
    10 rows in set (0.05 sec)

Don't be confused with MySQL here. The MySQL protocol and clients can be used to connect to
``searchd``, but there is no MySQL server itself.

Works? Ready? Now, it's time for :ref:`usage`!
