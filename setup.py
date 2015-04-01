#!/usr/bin/env python
from setuptools import setup

setup(
    name='ultradns',
    version='0.1.2',
    description='UltraDNS Client',
    author='Yola',
    author_email='engineers@yola.com',
    url='http://github.com/yola/ultradns',
    packages=['ultradns'],
    install_requires=['requests >= 1.0.0, < 2.0.0'],
)

