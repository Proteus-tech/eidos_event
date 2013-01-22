import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

from distutils.core import setup

setup(
    name='eidos_event',
    version='0.0.52',
    description='Event library for Eidos',
    author='Proteus Technologies',
    author_email='team@proteus-tech.com',
    url='http://proteus-tech.com',
    long_description = read('README.md'),
    # django is Eidos current version of django
    install_requires=['django>=1.3.1', 'django-serene>=0.0.5', 'gevent-socketio>=0.3.5-rc2', 'gunicorn==0.14.6', 'redis==2.6.2', 'django-celery==3.0.11', 'celery-with-redis==3.0'],
    dependency_links=['http://github.com/proteus-tech/django-logger/tarball/master#egg=django-logger-0.1'],
    package_data={'event': ['templates/*.html']},
    packages=['event', 'event.migrations', 'event.management', 'event.management.commands'],
)