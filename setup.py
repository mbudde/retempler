#!/usr/bin/env python

import os

from setuptools import setup

import retempler


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name='retempler',
    version=retempler.__version_string__,
    description='GTK program for renaming files',
    long_description=read('README.rst'),
    url='https://github.com/mbudde/',
    author='Michael Budde',
    author_email='mbudde@gmail.com',
    license='GPL v3',
    packages=['retempler'],
    scripts=['bin/retempler'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
    ],
    keywords=['rename', 'regex', 'gui' ,'gtk'],
    install_requires=['jinja2'],
)
