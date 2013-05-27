# -*- coding: utf-8 -*-

from sample_project.settings import *

DEBUG=False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'eidos_event',                      # Or path to database file if using sqlite3.
        'USER': 'eidos',                      # Not used with sqlite3.
        'PASSWORD': 'e1D05d6',                  # Not used with sqlite3.
        'HOST': '10.134.197.145',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

STATIC_ROOT = '/home/webapp/static/event/'
MEDIA_ROOT = '/home/webapp/media/event/'