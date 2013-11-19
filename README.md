eidos_event
===========

Event library for handling events for eidos

Additional Setup for requests library
======================================
From http://docs.python-requests.org/en/latest/user/install/?highlight=gevent

Installing Gevent
----------------- 

If you are using the requests.async module for making concurrent requests, you need to install gevent.

For OSX and Ubuntu, to install gevent, you’ll need libevent.

OSX:

>>> $ brew install libevent

Ubuntu:

>>> $ apt-get install libevent-dev

Once you have libevent, you can install gevent with pip:

>>> $ pip install gevent

For Windows, you don't need libevent, but you would need to use installer for the libraries. You can find both the gevent library library from http://www.lfd.uci.edu/~gohlke/pythonlibs/.
Install them and copy the library over into virtual environment