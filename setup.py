#!/usr/bin/env python
from setuptools import setup

setup(
    name='youltradns',
    version='0.0.1',
    description='Yola UltraDNS Client',
    author='Yola',
    author_email='engineers@yola.com',
    url='http://github.com/yola/youltradns',
    packages=['youltradns'],
    install_requires=['requests >= 1.0.0, < 2.0.0'],
)

