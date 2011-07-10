#!/usr/bin/python

import card_info as ci
import game
import random
import utils

def long_deck_composition_list(d):
    ret = []
    for card in ci.card_names():
        ret.append(d.get(card, 0))
    return ret

def score_deck_extractor(deck_comp):
    return game.score_deck(deck_comp)

def deck_size_deck_extractor(deck_comp):
    return sum(deck_comp.itervalues())

def action_balance_deck_extractor(deck_comp):
    ret = 0
    for card, quant in deck_comp.iteritems():
        ret += (ci.num_plus_actions(card) - ci.is_action(card)) * quant
    return ret / (sum(deck_comp.itervalues()) or 1)

def unique_deck_extractor(deck_comp):
    return len(deck_comp)
        
def get_matching_names(suffix):
    return [n[:-len(suffix)] for n in globals() if n.endswith(suffix)]

def get_matching_objects(suffix):
    return [eval(n) for n in globals() if n.endswith(suffix)]

DECK_FEATURE_NAMES = get_matching_names('deck_extractor')
DECK_FEATURE_EXTRACTORS = get_matching_objects('deck_extractor')

def outcome_common_extractor(g, game_state):
    turn_order = game_state.player_turn_order()
    return g.get_player_deck(turn_order[0]).WinPoints()

def turn_tiebreaker_common_extractor(g, game_state):
    current_turn_order = game_state.player_turn_order()
    return g.get_player_deck(current_turn_order[0]).TurnOrder()

def piles_empty_common_extractor(g, game_state):
    ret = 0
    for card, quant in game_state.supply().iteritems():
        if quant == 0:
            ret += 1
    return ret

def piles_low_common_extractor(g, game_state):
    ret = 0
    for card, quant in game_state.supply().iteritems():
        if quant <= 2:
            ret += 1
    return ret

def prov_or_colony_low_extractor(g, game_state):
    for card, quant in game_state.supply().iteritems():
        if (card == 'Province' or card == 'Colony') and 1 <= quant <= 2:
            return 1
    return 0

def turn_no_common_extractor(g, game_state):
    return game_state.turn_index()

COMMON_FEATURE_NAMES = get_matching_names('common_extractor')
COMMON_FEATURE_EXTRACTORS = get_matching_objects('common_extractor')

def encode_state_r_fmt(g, game_state):
    output_list = [g.get_id() + str(game_state.turn_index())]
    for common_extractor in COMMON_FEATURE_EXTRACTORS:
        output_list.append(common_extractor(g, game_state))
    
    for player_name in game_state.player_turn_order():
        deck_comp = game_state.get_deck_composition(player_name)
        for extractor in DECK_FEATURE_EXTRACTORS:
            output_list.append(extractor(deck_comp))
        output_list.extend(long_deck_composition_list(deck_comp))
    return output_list

def encode_diff(orig_state):
    ret = orig_state[:]
    common_info_size = len(COMMON_FEATURE_EXTRACTORS) + 1
    num_features = (len(ret) - common_info_size) / 2
    for ind in range(common_info_size, common_info_size + num_features):
        ret[ind + num_features] -= ret[ind]
    return ret

def output_state(state, output_file):
    formatted_str = ' '.join(map(str, state))
    output_file.write(formatted_str)
    output_file.write('\n')

def write_header(output_file):
    header = []
    header.extend(COMMON_FEATURE_NAMES)
    
    for player_label in ['s', 'o']:
        for feature_name in DECK_FEATURE_NAMES:
            header.append(player_label + feature_name)
        for card in ci.card_names():
            header.append(player_label + 
                          card.replace(' ', '_').replace("'", ''))
    output_file.write(' '.join(header) + '\n')

def main():
    c = utils.get_mongo_connection()

    output_file = open('r_format_test.data', 'w')
    output_file2 = open('r_format2_test.data', 'w')
    write_header(output_file)
    write_header(output_file2)
    
    for raw_game in utils.progress_meter(
        c.test.games.find({'_id': {'$gt': 'game-20110230'} }
                          ).limit(1000),1000):
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
        output_state(encode_diff(picked), output_file2)
                
if __name__ == '__main__':
    main()
