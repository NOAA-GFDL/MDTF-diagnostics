#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 15:00:00 2020

This file cleans up the existing repo tags following discussions contained in
https://github.com/PCMDI/cmip6-cmor-tables/issues/207

# Based on this script
https://github.com/WCRP-CMIP/CMIP6_CVs/blob/master/src/cleanupTags.py

# Using the method in this Stack Overflow post
https://stackoverflow.com/questions/21738647/change-date-of-git-tag-or-github-release-based-on-it

"""
import os,subprocess

# Create cleanup list
# git show-ref --tags
tagClean = []
tagClean.append('6.2.10.0')
tagClean.append('6.2.11.2')
tagClean.append('6.2.15.0')
tagClean.append('6.2.8.23')
tagClean.append('6.5.29')
tagClean.append('6.6.30')
tagClean.append('6.7.31')
tagClean.append('6.8.31')
tagClean.append('6.9.32')

# Iterate over list to delete existing tags
for count,tag in enumerate(tagClean):
    print('tag:    ',tag)
    # Git delete existing tag
    subprocess.call(['git','tag','-d',tag])
    # And push to remote
    subprocess.call(['git','push','origin',''.join([':refs/tags/',tag])])

# Create target dictionary
tagList = {}
# 6.2.24
tagList['6.2.24'] = {}
tagList['6.2.24']['Comment'] = 'CMIP6_CVs-6.2.8.23/DREQ-01.00.24/CMOR-3.3.3'
tagList['6.2.24']['MD5'] = '8eb3f1227afa76ae9db69d2affd1742c480c2031'
# 6.3.27
tagList['6.3.27'] = {}
tagList['6.3.27']['Comment'] = 'CMIP6_CVs-6.2.10.0/DREQ-01.00.27/CMOR-3.3.3'
tagList['6.3.27']['MD5'] = '26b4f2489c0448ed32c94d408f06cc380d640f89'
# 6.3.27-fixed
tagList['6.3.27-fixed'] = {}
tagList['6.3.27-fixed']['Comment'] = 'CMIP6_CVs-6.2.11.2/DREQ-01.00.27(modified)/CMOR-3.3.3'
tagList['6.3.27-fixed']['MD5'] = 'b427077cbca2c28b2948752c63e4d3f68449fc1f'
# 6.4.28
tagList['6.4.28'] = {}
tagList['6.4.28']['Comment'] = 'CMIP6_CVs-6.2.15.0/DREQ-01.00.28/CMOR-3.3.3'
tagList['6.4.28']['MD5'] = '96cd03b09264e07b1d1f5ab912eed085e23e30c2'
# 6.5.29
tagList['6.5.29'] = {}
tagList['6.5.29']['Comment'] = 'CMIP6_CVs-6.2.15.0/DREQ-01.00.29/CMOR-3.4.0'
tagList['6.5.29']['MD5'] = '0a4445523f2d2964ef37aaf2423691b218a00bee'
# 6.6.30
tagList['6.6.30'] = {}
tagList['6.6.30']['Comment'] = 'CMIP6_CVs-6.2.20.1/DREQ-01.00.30/CMOR-3.4.0'
tagList['6.6.30']['MD5'] = 'ea2a2f73ee859706c58b34f83df1d52b0b6c1798'
# 6.7.31
tagList['6.7.31'] = {}
tagList['6.7.31']['Comment'] = 'CMIP6_CVs-6.2.35.0/DREQ-01.00.31/CMOR-3.4.0'
tagList['6.7.31']['MD5'] = '02c87565bcac3c3fc916cd1e0f5242a68b588158'
# 6.8.31
tagList['6.8.31'] = {}
tagList['6.8.31']['Comment'] = 'CMIP6_CVs-6.2.35.3/DREQ-01.00.31/CMOR-3.5.0'
tagList['6.8.31']['MD5'] = '9f0ed59b7575331c0c25320cfa8bb7f0b722a2d6'
# 6.9.32
tagList['6.9.32'] = {}
tagList['6.9.32']['Comment'] = 'CMIP6_CVs-6.2.53.0/DREQ-01.00.32/CMOR-3.6.0'
tagList['6.9.32']['MD5'] = 'b73ef115532e5d177dd03f8f662fd262c8b688ba'

for tag in list(tagList.keys()):
    print('tag:    ',tag)
    print('comment:',tagList[tag]['Comment'])
    print('MD5:    ',tagList[tag]['MD5'])
    # Git checkout tag hash
    subprocess.call(['git','checkout',tagList[tag]['MD5']])
    # Get timestamp of hash
    cmd = 'git show --format=%aD|head -1'
    ps = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
    timestamp = ps.communicate()[0].rstrip().decode("utf-8")
    print(timestamp)
    # Generate composite command and execute
    cmd = 'GIT_COMMITTER_DATE="%s" git tag -a %s -m "%s"'%(timestamp, tag, tagList[tag]['Comment'])
    print(cmd)
    subprocess.call(cmd,shell=True) ; # Shell=True required for string
# And push all new tags to remote
subprocess.call(['git','push','--tags'])
