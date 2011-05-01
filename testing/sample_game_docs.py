#!/usr/bin/python

""" Copy a small subset of the parsed game documents to a testdata directory.

This directory will be checked into the source control and make it easy for
people to get a sample version of the site working on their own machines
for testing."""

import shutil
import os

sample_dates = [
    '20101015',  
    '20101115',
    '20101215',
    '20110115',
    '20110215',
    '20110315',
    '20110415',
    ]

for date in sample_dates:
    base_name = '%s-0.json' % date
    src_data = 'parsed_out/%s' % (base_name)
    targ_data = 'testing/testdata/%s' % base_name
    if os.path.exists(src_data):
        shutil.copy(src_data, targ_data)
    else:
        print src_data, 'does not exist'

