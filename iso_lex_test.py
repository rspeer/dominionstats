import unittest

import iso_lex

for token_type in iso_lex.tokens:
    locals()[token_type] = token_type

class LexCardsTest(unittest.TestCase):
    def test_lex_cards(self):
        lexed = iso_lex.type_lex('<span class=card-treasure>Coppers</span>\n')
        self.assertEquals(lexed, [CARD, NEWLINE])
        
        lexed = iso_lex.type_lex(
            'player1 <span class=card-treasure>Coppers</span>.')
        self.assertEquals(lexed, [PLAYER, CARD])

        lexed = iso_lex.type_lex(
            '... ... and plays the <span class=card-none>Throne Room</span> '
            'again.\n')
        self.assertEquals(lexed, [PLAYS, CARD, NEWLINE])

        lexed = iso_lex.type_lex(
             '... player1 gains the '
             '<span class=card-reaction>Watchtower</span>.')
        self.assertEquals(lexed, [PLAYER, GAINS, CARD])

        lexed = iso_lex.type_lex(
            '... player2 gains a <span class=card-treasure>Copper</span> '
             'and a <span class=card-curse>Curse</span>')
        self.assertEquals(lexed, [PLAYER, GAINS, CARD, CARD])

        lexed = iso_lex.type_lex(
            'player3 plays a <span class=card-treasure>Platinum</span>, '
            '3 <span class=card-treasure>Golds</span>, and a '
            '<span class=card-treasure>Copper</span>.')
        self.assertEquals(lexed, [PLAYER, PLAYS, CARD, NUMBER, CARD, CARD])

        lexed = iso_lex.type_lex(
            'cards in supply: <span cardname="Black Market" '
            'class=card-none>Black Market</span>, '
            '<span cardname="Caravan" class=card-duration>Caravan</span>')
        self.assertEquals(lexed, [CARD, CARD])

        lexed = iso_lex.type_lex(
             'player1 plays a <span class=card-none>Coppersmith</span>.')
        self.assertEquals(lexed, [PLAYER, PLAYS, CARD])
        
        lexed = iso_lex.type_lex(
             'player3 buys an <span class=card-none>Expand</span>')
        self.assertEquals(lexed, [PLAYER, BUYS, CARD])

if __name__ == '__main__':
    unittest.main()
