#!/usr/bin/python

import unittest
import game
import simplejson as json

class ScoreDeckTest(unittest.TestCase):
    def test_gardens(self):
        self.assertEquals(game.score_deck({'Gardens': 1, 'Copper': 9}), 1)
        self.assertEquals(game.score_deck({'Gardens': 2, 'Copper': 8}), 2)
        self.assertEquals(game.score_deck({'Gardens': 2, 'Copper': 7}), 0)

    def test_fairgrounds(self):
        self.assertEquals(game.score_deck({'Fairgrounds': 1,
                                           'Copper': 1,
                                           'Silver': 1,
                                           'Gold': 1,
                                           'Bank': 1}), 2)

    def test_duke(self):
        self.assertEquals(game.score_deck({'Duke': 2, 'Duchy': 2}), 10)

    def test_simple(self):
        self.assertEquals(game.score_deck({
                    'Curse': 1, 'Estate': 1, 'Duchy': 1, 
                    'Province': 1, 'Colony': 1}), 19)

    def test_vineyards(self):
        self.assertEquals(game.score_deck({'Vineyard': 2, 'Jester': 3,
                                           'Fishing Village': 3}), 4)

class GameStateTest(unittest.TestCase):
    def _get_turn_labels(self, game_state_it):
        return [game_state_it.turn_label() for t in game_state_it]

    def test_turn_labels(self):
        raw_outpost_game = json.loads(open(
                'testing/testdata/sample_outpost_game.json', 'r').read())
        outpost_game = game.Game(raw_outpost_game)
        turn_labels = self._get_turn_labels(outpost_game.game_state_iterator())
        for game_state in outpost_game.game_state_iterator():
            pass

if __name__ == '__main__':
    unittest.main()
