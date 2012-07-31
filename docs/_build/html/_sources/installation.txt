.. _installation:

Installation
============

So, you want to try **Sphinxit**? Good! Installation is simple as always with ``pip``::

	$ pip install sphinxit


Do it in your project`s virtualenv... you know. Or, you can grab 
`latest code from Github <https://github.com/semirook/sphinxit>`_. Just::

	$ pip install -e git+https://github.com/semirook/sphinxit#egg=sphinxit


The only dependency of Sphinxit is ``MySQLdb`` library. Usually it`s ``python-mysqldb`` package
and you can install it with your system package manager or with pip, but it`s not true for all systems.
For OS X it`s ``mysql-python`` package, for example. Maybe, MySQLdb is already installed 
in your system, check it.

What`s next? Visit :ref:`quickstart` to learn more.