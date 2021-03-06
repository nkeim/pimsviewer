import os
from setuptools import setup

try:
    descr = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()
except IOError:
    descr = ''

try:
    from pypandoc import convert

    descr = convert(descr, 'rst', format='md')
except ImportError:
    pass

setup_parameters = dict(
    name="pimsviewer",
    version='1.0',
    description="Viewer for Python IMage Sequence (PIMS).",
    author="Casper van der Wel",
    author_email="caspervdw@gmail.com",
    url="https://github.com/soft-matter/pimsviewer",
    install_requires=['scikit-image>=0.11', 'matplotlib', 'pims>=0.4',
                      'pillow'],
    packages=['pimsviewer'],
    long_description=descr,
)

setup(**setup_parameters)
