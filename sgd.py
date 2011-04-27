from utils import get_mongo_connection
from game import Game, PlayerDeck
import card_info
from scikits.learn.linear_model import SGDClassifier
from collections import defaultdict
import numpy as np

con = get_mongo_connection()
DB = con.test
games = DB.games

MAX_TURNS = 25
REQUIRED_PLAYERS = 2
#BATCH_SIZE = 10000

CARDS = sorted(card_info._card_info_rows.keys())
CARDS_INDEX = {}
for i, card in enumerate(CARDS):
    CARDS_INDEX[card] = i
NCARDS = len(CARDS)

def decks_by_turn(game):
    turn_ordered_players = sorted(game.PlayerDecks(),
                                  key=PlayerDeck.TurnOrder)
    nplayers = len(turn_ordered_players)
    turn_num = 1
    player_num = 0
    for state in game.GameStateIterator():
        player = turn_ordered_players[player_num].player_name
        balanced_points = turn_ordered_players[player_num].WinPoints() - 1
        yield (turn_num, state.player_decks[player], balanced_points)

        player_num += 1
        if (player_num == nplayers):
            player_num = 0
            turn_num += 1
        if turn_num > MAX_TURNS:
            break

def deck_to_vector(deck):
    vec = np.zeros((NCARDS,))
    for card, count in deck.items():
        idx = CARDS_INDEX[card]
        vec[idx] = count
    if np.sum(vec) == 0:
        # watch out for the masquerade trick
        return zero_vector()
    else:
        return vec / np.sum(vec)

def zero_vector():
    return np.zeros((NCARDS,))

def should_learn(game):
    return (len(game.player_decks) == REQUIRED_PLAYERS and
            game.player_decks[0].win_points != 1.0)

def run_sgd():
    classifiers = [
      SGDClassifier(loss='log', fit_intercept=0, n_iter=10, verbose=True)
      for i in xrange(MAX_TURNS)
    ]
    training_vecs = defaultdict(list)
    training_values = defaultdict(list)
    iter = 0
    out = open('card_values.txt', 'w')
    for gamedata in games.find():
        iter += 1
        game = Game(gamedata)
        if should_learn(game):
            turn_vecs = defaultdict(zero_vector)
            turn_counts = defaultdict(int)
            for turn_num, deck_state, points in decks_by_turn(game):
                vec = deck_to_vector(deck_state)
                turn_vecs[turn_num] += vec * points
                turn_counts[turn_num] += 1

            for turn_num in turn_counts:
                if turn_counts[turn_num] == REQUIRED_PLAYERS:
                    vec = turn_vecs[turn_num]
                    training_vecs[turn_num].extend([vec, -vec])
                    training_values[turn_num].extend([1, 0])
        if iter % 10000 == 0:
            print iter

    for turn_num in xrange(1, MAX_TURNS):
        coef_init = getattr(classifiers[turn_num],
                            'coef_',
                            zero_vector())
                            
        classifiers[turn_num].fit(training_vecs[turn_num],
                                  training_values[turn_num],
                                  coef_init = coef_init)

    for card_num in xrange(NCARDS):
        card = CARDS[card_num]
        weights = [str(classifiers[i].coef_[card_num]) for i in xrange(2, MAX_TURNS)]
        row = [card]+weights
        print >> out, ','.join(row)
        print ','.join(row)

if __name__ == '__main__':
    run_sgd()
