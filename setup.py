import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

from distutils.core import setup

setup(
    name='eidos_event',
    version='0.0.5',
    description='Event library for Eidos',
    author='Proteus Technologies',
    author_email='team@proteus-tech.com',
    url='http://proteus-tech.com',
    long_description = read('README.md'),
    # django is Eidos current version of django
    install_requires=['django==1.3.1', 'djangorestframework>=0.3.3', 'django-serene>=0.0.5'],
#    package_data={'restful': ['templates/restful/*.html']},
    packages=['event','event.templates'],
)