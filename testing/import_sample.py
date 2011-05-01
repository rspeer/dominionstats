#!/usr/bin/python

""" Copy testing game documents into mongo."""

import os
import pymongo
import pprint
import simplejson as json

conn = pymongo.Connection()
games_coll = conn.test.games

games_path = os.path.join('testing', 'testdata')

for fn in os.listdir(games_path):
    full_path = os.path.join(games_path, fn)
    print 'importing from', full_path
    game_docs = json.load(open(full_path, 'r'))
    for ind, game_doc in enumerate(game_docs):
        try:
            games_coll.insert(game_doc)
        except Exception, e:
            print game_doc['_id'], e
            continue


        
