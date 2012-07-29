.. _quickstart:

Quickstart
==========

Eager to get started?  This page gives a good introduction to Flask.  It
assumes you already have Flask installed.  If you do not, head over to the
:ref:`installation` section.


A minimal Flask application looks something like this::

    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def hello_world():
        return 'Hello World!'

    if __name__ == '__main__':
        app.run()

Just save it as `hello.py` (or something similar) and run it with your Python
interpreter.  Make sure to not call your application `flask.py` because this
would conflict with Flask itself.