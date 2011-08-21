#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Convert game documents to a format easily readable by R."""

import itertools

import card_info as ci
import game
import random
import utils

def declare_multi_feature_extractor(feature_names):
    def dec(func):
        def wrapped(*args):
            ret = func(*args)
            assert len(ret) == len(wrapped.feature_names)
            return ret
        wrapped.feature_names = [f.replace(' ', '_') for f in feature_names]
        return wrapped
    return dec

@declare_multi_feature_extractor(ci.card_names())
def composition_deck_extractor(deck_comp, game_state, player):
    ret = []
    for card in ci.card_names():
        ret.append(deck_comp.get(card, 0))
    return ret

def score_deck_extractor(deck_comp, game_state, player):
    return [game_state.player_score(player)]

def deck_size_deck_extractor(deck_comp, game_state, player):
    return [sum(deck_comp.itervalues())]

def action_balance_deck_extractor(deck_comp, game_state, player):
    ret = 0
    for card, quant in deck_comp.iteritems():
        ret += (ci.num_plus_actions(card) - ci.is_action(card)) * quant
    return [ret / (sum(deck_comp.itervalues()) or 1)]

def unique_deck_extractor(deck_comp, game_state, player):
    return [len(deck_comp)]

def outcome_common_extractor(g, game_state):
    turn_order = game_state.player_turn_order()
    return [g.get_player_deck(turn_order[0]).WinPoints()]

def turn_tiebreaker_common_extractor(g, game_state):
    current_turn_order = game_state.player_turn_order()
    return [g.get_player_deck(current_turn_order[0]).TurnOrder()]

def num_piles_empty_common_extractor(g, game_state):
    ret = 0
    for card, quant in game_state.supply.iteritems():
        if quant == 0:
            ret += 1
    return [ret]

def num_piles_low_common_extractor(g, game_state):
    ret = 0
    for card, quant in game_state.supply.iteritems():
        if quant <= 2:
            ret += 1
    return [ret]

def prov_or_colony_low_extractor(g, game_state):
    for card, quant in game_state.supply.iteritems():
        if (card == 'Province' or card == 'Colony') and 1 <= quant <= 2:
            return [1]
    return [0]

def turn_no_common_extractor(g, game_state):
    return [game_state.turn_index()]

@declare_multi_feature_extractor(ci.card_names())
def supply_common_extractor(g, game_state):
    ret = []
    for card in ci.card_names():
        ret.append(game_state.supply.get(card, 0))
    return ret

def make_extractor_list(suffix):
    extractor_names = [n[:-len(suffix)] for n in 
                       globals() if n.endswith(suffix)]
    extractors = [eval(n + suffix) for n in extractor_names]
    for extractor, name in itertools.izip(extractors, extractor_names):
        if not hasattr(extractor, 'feature_names'):
            extractor.feature_names = [name] 
    return extractors

_deck_extractor_list = make_extractor_list('deck_extractor')
_common_extractor_list = make_extractor_list('common_extractor')

def feature_names(feature_extractor_list):
    ret = []
    for extractor in feature_extractor_list:
        ret.extend(extractor.feature_names)
    return ret

def encode_state_r_fmt(g, game_state, encode_id=False):
    output_list = []
    if encode_id:
        assert False
        output_list.append(g.get_id() + '#' + 
                           game_state.turn_label(for_anchor=True))

    for common_extractor in _common_extractor_list:
        output_list.extend(common_extractor(g, game_state))
    
    per_player_features = []
    for player_name in game_state.player_turn_order():
        cur_player_features = []
        deck_comp = game_state.get_deck_composition(player_name)
        for extractor in _deck_extractor_list:
            cur_player_features.extend(
                extractor(deck_comp, game_state, player_name))
        output_list.extend(cur_player_features)
        per_player_features.append(cur_player_features)

    p1, p2 = per_player_features
    for p1_feature_val, p2_feature_val in itertools.izip(p1, p2):
        output_list.append(p1_feature_val - p2_feature_val)
    
    return output_list

def output_state(state, output_file):
    formatted_str = u' '.join(map(unicode, state))
    actual = formatted_str.count(' ') 
    expected = len(make_header()) - 1
    assert actual == expected, '%s %d %d' % (state[0], actual, expected)
    output_file.write(formatted_str)
    output_file.write('\n')

def make_header():
    header = feature_names(_common_extractor_list)
    
    for player_label in ['my', 'opp', 'diff']:
        for feature_name in feature_names(_deck_extractor_list):
            header.append(player_label + '_' + feature_name)
                           
    return header

def write_header(output_file):
    outputted = ' '.join(make_header()) + '\n'
    output_file.write(outputted)

def main():
    c = utils.get_mongo_connection()

    output_file = open('r_format.data', 'w')
    write_header(output_file)
    
    for raw_game in utils.progress_meter(
        c.test.games.find(
            #{'_id': {'$gt': 'game-20110230'} }
            ), 1000):
        g = game.Game(raw_game)
        if g.dubious_quality() or len(g.get_player_decks()) != 2:
            continue

        encoded_states = []
        for game_state in g.game_state_iterator():
            encoded_state_list = encode_state_r_fmt(g, game_state)
            encoded_states.append(encoded_state_list)

        # only pick one state from each game to avoid overfitting.
        picked = random.choice(encoded_states)
        output_state(picked, output_file)
                
if __name__ == '__main__':
    main()
