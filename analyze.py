 #!/usr/bin/python

from __future__ import division

import card_info
from stats import MeanVarStat
from game import Game, PlayerDeck, Turn
import pymongo
import collections
import copy
import os
import pprint
import simplejson as json
import sys
import primitive_util
import argparse
import utils

PrimitiveConversion = primitive_util.PrimitiveConversion
ConvertibleDefaultDict = primitive_util.ConvertibleDefaultDict

parser = utils.IncrementalDateRangeCmdLineParser()
parser.add_argument('--small_run', type=bool, default=False)
parser.add_argument('--output_collection_name', default='analysis')

class CardStatistic(PrimitiveConversion):
    def __init__(self):
        self.available = 0
        self.win_any_accum = MeanVarStat()
        self.win_weighted_accum = MeanVarStat()
        self.win_weighted_accum_turn = ConvertibleDefaultDict(MeanVarStat, int)
        self.win_diff_accum = ConvertibleDefaultDict(MeanVarStat, int)

    def __repr__(self):
        ret = 'avail: %s/%d' % (self.win_any_accum, self.available)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def Compare(self, other):
        ret = ''
        for k, v in self.__dict__.iteritems():
            try:
                if self.__dict__[k] != other.__dict__[k]:
                    ret += k + '\n'
            except TypeError, t:
                ret += k + ' ' + t.message + '\n'
        return ret
        
class GamesAnalysis(PrimitiveConversion):
    def __init__(self):
        self.card_stats = ConvertibleDefaultDict(CardStatistic)
        self.num_games = 0
        self.max_game_id = ''
        
    def AnalyzeGame(self, game):
        self.num_games += 1
        seen_cards_players = set()
        self.max_game_id = max(self.max_game_id, game.Id())
        for card in game.Supply() + card_info.EVERY_SET_CARDS:
            self.card_stats[card].available += len(game.PlayerDecks())

        accumed_by_player = collections.defaultdict(
            lambda : collections.defaultdict(int))
        for turn in game.Turns():
            deck = turn.Player()
            turnno = turn.TurnNo()
            for card in turn.PlayerAccumulates():
                per_card_stat = self.card_stats[card]
                if (deck, card) not in seen_cards_players:
                    seen_cards_players.add((deck, card))
                    per_card_stat.win_any_accum.AddOutcome(deck.WinPoints())
                per_card_stat.win_weighted_accum.AddOutcome(deck.WinPoints())
                per_card_stat.win_weighted_accum_turn[turnno].AddOutcome(
                    deck.WinPoints())
                accumed_by_player[deck][card] += 1
                
        for deck, card_accum_dict in accumed_by_player.iteritems():
            total_other_decks = collections.defaultdict(int)
            odeck_count = 0
            for other_deck, other_accum in accumed_by_player.iteritems():
                if other_deck != deck:
                    odeck_count += 1
                    for card in other_accum:
                        total_other_decks[card] += other_accum[card]
            assert odeck_count != 0, game.IsotropicUrl()
            for card in set(card_accum_dict.keys() + total_other_decks.keys()):
                per_card_stat = self.card_stats[card]
                other_avg_freq = total_other_decks[card] / odeck_count
                card_diff_index = int(card_accum_dict[card] - other_avg_freq)
                #if card == 'Curse' and card_diff_index == 3:
                #    print game.IsotropicUrl()
                per_card_stat.win_diff_accum[card_diff_index].AddOutcome(
                    deck.WinPoints())

    def FormatCardStats(self):
        card_stats_list = list(self.card_stats.items())
        card_stats_list.sort(key = lambda name_stat_pair: 
                             -name_stat_pair[1].win_any_accum.Mean())
        for name, card_stat in card_stats_list:
            print name, card_stat.win_any_accum.Mean(), \
                card_stat.win_weighted_accum.Mean()

def main():
    args = parser.parse_args()

    c = pymongo.Connection()
    db = c.test
    games = db.games

    output_collection_name = args.output_collection_name
    output_collection = db[output_collection_name]
    game_analysis = GamesAnalysis()
    args.startdate = 'game-' + args.startdate
    args.enddate = 'game-' + args.enddate

    wrapper = primitive_util.PersistentIncrementalWrapper(game_analysis, '',
                                                          output_collection)
    print 'analysis includes', game_analysis.num_games, 'games'
    print 'with max game no', game_analysis.max_game_id

    query = {'_id': {'$gt': args.startdate,
                     '$lt': args.enddate}}

    if args.small_run:
        assert 'rrenaud broke support for this' and False

    output_file_name = 'static/output/all_games_card_stats.js'
    # if args.small_run:
    #     coll.limit(100)
    #     output_file_name = 'static/output/sample_games_card_stats.js'
    # else:
    #     output_file_name = 'static/output/all_games_card_stats.js'

    if not os.path.exists('static/output'):
        os.makedirs('static/output')
    
    for idx, g in enumerate(wrapper.Scan(games, query)):
        try:
            if idx % 1000 == 0:
                print idx
            game_analysis.AnalyzeGame(Game(g))
        except int, e:
            print Game(g).IsotropicUrl()
            print g
            raise 

    wrapper.Save()
    output_file = open(output_file_name, 'w')
    output_file.write('var all_card_data = ')

    json.dump(game_analysis.ToPrimitiveObject(), output_file)

if __name__ == '__main__':
    main() 
