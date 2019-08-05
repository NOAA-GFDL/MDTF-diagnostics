#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.md", 'r') as f:
    long_description = f.read()

packages = find_packages()

setup(
   name='MDTF-diagnostics',
   version='2.1',
   description='Process-oriented diagnostics for weather and climate simulations',
   license='LGPLv3',
   long_description=long_description,
   long_description_content_type='text/markdown',
   author='MDTF Collaboration',
   author_email='thomas.jackson@noaa.gov',
   url="https://github.com/NOAA-GFDL/MDTF-diagnostics",
   classifiers=[
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
   ],
   scripts=[
       'mdtf.py'
   ],
   packages=packages
#   install_requires=[...] #external packages as dependencies
)
