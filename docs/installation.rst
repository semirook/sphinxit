.. _installation:

Installation
============

So, you want to try **Sphinxit**? Great! Installation is simple as usual with ``pip``::

    $ pip install sphinxit

Or you can grab the `latest codebase from Github <https://github.com/semirook/sphinxit>`_. Just::

    $ pip install -e git+https://github.com/semirook/sphinxit#egg=sphinxit

If you prefer this way of package managing, you have to install some dependencies too. 
You can find full list of them in the `reqs.pip` file::

    $ pip install -r reqs.pip

to complete manual installation. The only Sphinxit dependencies are:

* ``oursql`` (MySQL client);
* ``six`` (Python 2 and 3 compatibility layer);
* ``ordereddict`` if you're stuck with Python 2.6.
