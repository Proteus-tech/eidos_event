import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

from distutils.core import setup

setup(
    name='eidos_event',
    version='0.0.30',
    description='Event library for Eidos',
    author='Proteus Technologies',
    author_email='team@proteus-tech.com',
    url='http://proteus-tech.com',
    long_description = read('README.md'),
    # django is Eidos current version of django
    install_requires=['django>=1.3.1', 'django-serene>=0.0.5'],
    dependency_links=['http://github.com/proteus-tech/django-logger/tarball/master#egg=django-logger-0.1', 'http://github.com/abourget/gevent-socketio/tarball/master#egg=gevent-socketio-0.3.5-rc2'],
    package_data={'event': ['templates/*.html']},
    packages=['event', 'event.migrations'],
)