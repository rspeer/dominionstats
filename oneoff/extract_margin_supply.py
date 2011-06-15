#!/usr/bin/python

import sys
sys.path.append('../')
import utils
import game

def first_player_margin(g):
    turn_ordered_players = sorted(g.get_player_decks(),
                                  key=game.PlayerDeck.TurnOrder)
    f, s = turn_ordered_players
    turn_penalty = (f.num_turns() == s.num_turns()) * .5
    return f.Points() - s.Points() - turn_penalty

def main():
    db = utils.get_mongo_database()
    game_summaries = []
    output_fn = open('margin.txt', 'w')
    for idx, raw_game in enumerate(
        utils.progress_meter(db.games.find({}), 1000)):
        g = game.Game(raw_game)
        if g.dubious_quality():
            continue
        if len(g.get_player_decks()) != 2:
            continue
        output_fn.write('%f:%s\n' % (first_player_margin(g), 
                                   ','.join(g.get_supply())))

if __name__ == "__main__":
    main()
