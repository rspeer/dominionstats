#!/usr/bin/python

import pymongo
import random
import trueskill

PLAYER_SKILLS = (12, 8, 6)
(GOOD_P, OKAY_P, BAD_P) = PLAYER_SKILLS

OPENING_STRENGTHS = (2, 0, -2)
(GOOD_O, OKAY_O, BAD_O) = OPENING_STRENGTHS

def ChooseFromDist(labels, weights):
    r = random.random()
    for l, w in zip(labels, weights):
        if w > r:
            return l
        r -= w

def SamplePlayerOpening():
    p = random.choice(PLAYER_SKILLS)
    if p == GOOD_P:
        o = ChooseFromDist(OPENING_STRENGTHS, [.2, .2, .6])
    else:
        o = ChooseFromDist(OPENING_STRENGTHS, [.3, .3, .4])
    return p, o

def SimTeam(t):
    return random.random() * t[0] + t[1]

def SimGame(t1, t2):
    return SimTeam(t1) > SimTeam(t2)

def encode_team(t):
    return 'player' + str(t[0]),  'open:' + str(t[1])

def encode_player(t):
    return ('player' + str(t[0]),)

def sim_games(credit_assignment, blame, coll):
    for i in range(1000):
        t1, t2 = SamplePlayerOpening(), SamplePlayerOpening()
        out = SimGame(t1, t2)
        ranks = [0, 1]
        if not out:
            print t2, 'beats2', t1
            ranks.reverse()
        else:
            print t1, 'beats1', t2

        trueskill.db_update_trueskill(
            [(credit_assignment(t1), blame, ranks[0]),
             (credit_assignment(t2), blame, ranks[1])],
            coll)
    

def main():
    c = pymongo.Connection()
    coll = c.skill_test.skill

    sim_games(encode_player, [1.0], coll)
    sim_games(encode_team, [.5, .5], coll)

if __name__ == '__main__':
    main()
