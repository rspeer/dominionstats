#!/usr/bin/python
# -*- coding: utf-8 -*-
import unittest
import parse_game
import pprint

class CaptureCardsTest(unittest.TestCase):
    def testCaptureCards(self):
        captured = parse_game.CaptureCards(
            'Hawk plays 3 <span class=card-treasure>Coppers</span>.')
        self.assertEquals(captured, ['Copper'] * 3)
        
        captured = parse_game.CaptureCards(
            '... ... and plays the <span class=card-none>Throne Room</span> '
            'again.')
        self.assertEquals(captured, ['Throne Room'])

        captured = parse_game.CaptureCards(
            '... darthfatty gains the '
            '<span class=card-reaction>Watchtower</span>.')
        self.assertEquals(captured, ['Watchtower'])

        captured = parse_game.CaptureCards(
            '... jpax73 gains a <span class=card-treasure>Copper</span> '
            'and a <span class=card-curse>Curse</span>')
        self.assertEquals(captured, ['Copper', 'Curse'])

        captured = parse_game.CaptureCards(
            'pauljh plays a <span class=card-treasure>Platinum</span>, '
            '3 <span class=card-treasure>Golds</span>, and a '
            '<span class=card-treasure>Copper</span>.')
        self.assertEquals(captured, ['Platinum', 'Gold', 'Gold', 'Gold',
                                     'Copper'])

        captured = parse_game.CaptureCards(
            'cards in supply: <span cardname="Black Market" '
            'class=card-none>Black Market</span>, '
            '<span cardname="Caravan" class=card-duration>Caravan</span>')
        self.assertEquals(captured, ['Black Market', 'Caravan'])

        captured = parse_game.CaptureCards(
            'Alenia plays a <span class=card-none>Coppersmith</span>.')
        self.assertEquals(captured, ['Coppersmith'])
        
        captured = parse_game.CaptureCards(
            'fairgr buys an <span class=card-none>Expand</span>')
        self.assertEquals(captured, ['Expand'])

class NameAndRestTest(unittest.TestCase):
    def testNameAndRest1(self):
        name, rest = parse_game.NameAndRest(
 "... Gypsy Steward trashes a <span class=card-treasure>Copper</span>.", 
 "trashes")
        self.assertEquals(name, "Gypsy Steward")
        self.assertEquals(rest, " a <span class=card-treasure>Copper</span>.")

    def testNameAndRest2(self):
        name, rest = parse_game.NameAndRest(
" ... rrenaud trashes an <span class=card-victory>Estate</span> and gets +1 ▼.",
"trashes")
        self.assertEquals(name, 'rrenaud')
        self.assertEquals(rest, 
" an <span class=card-victory>Estate</span> and gets +1 ▼.")

class ParseTurnTest(unittest.TestCase):
    def testParseTurn(self):
        turn_info = parse_game.ParseTurn(
u"""--- Hawk's turn 3 ---
   Hawk plays 3 <span class=card-treasure>Coppers</span>.
   Hawk buys a <span class=card-treasure>Silver</span>.
   <span class=logonly>(Hawk draws: an <span class=card-victory>Estate</span> and 4 <span class=card-treasure>Coppers</span>.)</span>
""")
        self.assertEquals(turn_info['name'], 'Hawk')
        self.assertEquals(turn_info['plays'], ['Copper', 'Copper', 'Copper'])
        self.assertEquals(turn_info['buys'], ['Silver'])
        self.assertEquals(turn_info['money'], 3)

    def testChapelTurn(self):
        turn_info = parse_game.ParseTurn(
u"""--- Kiyogi's turn 4 ---
Kiyogi plays a <span class=card-none>Chapel</span>.
... trashing 2 <span class=card-treasure>Coppers</span>.
(Kiyogi reshuffles.)""")
        self.assertEquals(turn_info['plays'], ['Chapel'])
        self.assertEquals(turn_info['trashes'], ['Copper', 'Copper'])
        self.assertTrue('opp' not in turn_info)

    def testBishopTurn(self):
        turn_info = parse_game.ParseTurn(
u"""--- Gypsy Steward's turn 7 ---
Gypsy Steward plays a <span class=card-none>Bishop</span>.
... getting +$1 and +1 ▼.
... Gypsy Steward trashes a <span class=card-treasure>Copper</span>.
... duchyduke trashes a <span class=card-treasure>Copper</span>.
Gypsy Steward plays 3 <span class=card-treasure>Coppers</span>.
Gypsy Steward buys a <span class=card-treasure>Silver</span>.""")
        self.assertEquals(turn_info['plays'], ['Bishop', 'Copper', 
                                               'Copper', 'Copper'])
        self.assertEquals(turn_info['trashes'], ['Copper'])
        self.assertEquals(turn_info['money'], 4)

    def testBishopTurn2(self):
        turn_info = parse_game.ParseTurn(
"""--- rrenaud's turn 3 ---
 rrenaud plays a <span class=card-none>Bishop</span>.
 ... getting +$1 and +1 ▼.
 ... rrenaud trashes an <span class=card-victory>Estate</span> and gets +1 ▼.
 ... kristi trashes nothing.
 rrenaud plays 3 <span class=card-treasure>Coppers</span>.
 rrenaud buys a <span class=card-none>Throne Room</span>.""")
        self.assertEquals(turn_info['trashes'], ['Estate'])
        self.assertTrue('opp' not in turn_info)
        self.assertEquals(turn_info['money'], 4)

    def testBishopTurn3(self):
        turn_info = parse_game.ParseTurn(
"""   --- kristi's turn 4 ---
    kristi plays a <span class=card-none>Bishop</span>.
    ... getting +$1 and +1 ▼.
    ... kristi trashes an <span class=card-victory>Estate</span> and gets +1 ▼.
    ... rrenaud trashes a <span class=card-treasure>Copper</span>.""")
        self.assertEquals(turn_info['trashes'], ['Estate'])
        self.assertEquals(turn_info['opp']['rrenaud']['trashes'], 
                          ['Copper'])
        self.assertEquals(turn_info['money'], 1)

    def testMineUpgradeTurn(self):
        turn_info = parse_game.ParseTurn(u"""--- rrenaud's turn 12 ---
rrenaud plays a <span class=card-none>Mine</span>.
... trashing a <span class=card-treasure>Talisman</span> and gaining a <span class=card-treasure>Gold</span>.
rrenaud plays a <span class=card-treasure>Gold</span>, a <span class=card-treasure>Royal Seal</span>, and a <span class=card-treasure>Copper</span>.
rrenaud plays a <span class=card-treasure>Loan</span>.
... drawing and revealing a <span class=card-none>Smithy</span> and then a <span class=card-treasure>Platinum</span>.
... discarding the <span class=card-treasure>Platinum</span>.
rrenaud buys a <span class=card-treasure>Gold</span>.
... putting the <span class=card-treasure>Gold</span> on top of the deck.
<span class=logonly>(rrenaud draws: 2 <span class=card-treasure>Golds</span>, 2 <span class=card-victory>Estates</span>, and a <span class=card-treasure>Silver</span>.)</span> """)
        self.assertEquals(turn_info['gains'], ['Gold'])
        self.assertEquals(turn_info['buys'], ['Gold'])
        self.assertEquals(turn_info['money'], 7)

    def testAmbassadorTurn(self):
        turn_info = parse_game.ParseTurn(
u"""        --- feelingzwontfade's turn 3 ---
feelingzwontfade plays an <span class=card-none>Ambassador</span>.
... feelingzwontfade reveals an <span class=card-victory>Estate</span>.
... returning 2 copies to the supply.
... (bgg-1) CurSeS gains an <span class=card-victory>Estate</span>.
<span class=logonly>(feelingzwontfade draws: an <span class=card-victory>Estate</span> and 4 <span class=card-treasure>Coppers</span>.)</span>
""")
        self.assertEquals(turn_info['name'], 'feelingzwontfade')
        self.assertEquals(turn_info['plays'], ['Ambassador'])
        self.assertEquals(turn_info['returns'], ['Estate', 'Estate'])
        self.assertEquals(turn_info['opp']['(bgg-1) CurSeS']['gains'],
                          ['Estate'])

    def testAmbassadorSecretChamberResponseTurn(self):
        turn_info = parse_game.ParseTurn(
u"""   --- hughes's turn 16 ---
   hughes plays an <span class=card-none>Ambassador</span>.
   ... Talia reveals a <span class=card-reaction>Secret Chamber</span>.
   ... ... drawing 2 cards.
   ... ... returning 2 cards to the deck.
   ... hughes reveals a <span class=card-treasure>Copper</span>.
   ... returning 2 copies to the supply.
   ... Talia gains a <span class=card-treasure>Copper</span>.""")
        self.assertEquals(turn_info['name'], 'hughes')
        self.assertEquals(turn_info['plays'], ['Ambassador'])
        self.assertEquals(turn_info['returns'], ['Copper', 'Copper'])
        self.assertEquals(turn_info['opp']['Talia']['gains'], ['Copper'])

    def testAmbassador3(self):
        turn_info = parse_game.ParseTurn(
"""   --- hughes's turn 6 ---
   hughes plays an <span class=card-none>Ambassador</span>.
   ... hughes reveals a <span class=card-treasure>Copper</span>.
   ... returning it to the supply.
   ... Talia gains a <span class=card-treasure>Copper</span>.""")
        self.assertEquals(turn_info['returns'], ['Copper'])
        self.assertEquals(turn_info['opp']['Talia']['gains'], ['Copper'])

    def testAmbassador4(self):
        turn_info = parse_game.ParseTurn(
"""--- rrenaud's turn 4 ---
rrenaud plays an <span class=card-none>Ambassador</span>.
... revealing 2 <span class=card-treasure>Coppers</span> and returning them to the supply.
... Torgen gains a <span class=card-treasure>Copper</span>.
""")
        self.assertEquals(turn_info['returns'], ['Copper', 'Copper'])

    def testAmbassador5(self):
        turn_info = parse_game.ParseTurn("""--- rrenaud's turn 8 ---
rrenaud plays a <span class=card-none>Worker's Village</span>.
... drawing 1 card and getting +2 actions and +1 buy.
rrenaud plays an <span class=card-none>Ambassador</span>.
... revealing a <span class=card-treasure>Copper</span> and returning it to the supply.
... Torgen gains a <span class=card-treasure>Copper</span>.
rrenaud plays an <span class=card-none>Ambassador</span>.
... revealing nothing and returning them to the supply.
... Torgen gains a <span class=card-treasure>Copper</span>.
""")
        self.assertEquals(turn_info['returns'], ['Copper'])
        self.assertEquals(turn_info['opp']['Torgen']['gains'], 
                          ['Copper', 'Copper'])

    def testTradingPostTurn(self):
        turn_info = parse_game.ParseTurn(
"""--- Apollo's turn 11 ---
Apollo plays a <span class=card-none>Trading Post</span>.
      ... Apollo trashes a <span class=card-treasure>Copper</span> and an <span class=card-victory>Estate</span>, gaining a <span class=card-treasure>Silver</span> in hand.
      Apollo plays a <span class=card-treasure>Copper</span> and a <span class=card-treasure>Silver</span>.
      Apollo buys a <span class=card-treasure>Silver</span>.
      (Apollo reshuffles.)
      <span class=logonly>(Apollo draws: 2 <span class=card-curse>Curses</span>, a <span class=card-treasure>Copper</span>, a <span class=card-none>Trading Post</span>, and a <span class=card-none>Laboratory</span>.)</span>""")
        self.assertEquals(turn_info['trashes'], ['Copper', 'Estate'])
        self.assertEquals(turn_info['money'], 3)

    def testSeaHagTurn(self):
        turn_info = parse_game.ParseTurn(
"""--- doh's turn 14 ---
    doh plays a <span class=card-none>Sea Hag</span>.
    ... Dave discards a <span class=card-none>Courtyard</span> and gains a <span class=card-curse>Curse</span> on top of the deck.""")
        self.assertEquals(turn_info['opp']['Dave']['gains'], ['Curse'])

    def testSeaHagTurn2(self):
        turn_info = parse_game.ParseTurn("""
  --- Kemps's turn 6 ---
    Kemps plays a <span class=card-none>Sea Hag</span>.
    ... BaconSnake discards nothing and gains a <span class=card-curse>Curse</span> on top of the deck.
    Kemps plays a <span class=card-treasure>Copper</span> and a <span class=card-treasure>Quarry</span>.
    Kemps buys a <span class=card-none>Cutpurse</span>.
""")
        self.assertEquals(turn_info['opp']['BaconSnake']['gains'], ['Curse'])
        self.assertEquals(turn_info['money'], 2)

    def testPirateShipTurn(self):
        turn_info = parse_game.ParseTurn(
u"""--- Luana's turn 7 ---
Luana plays a <span class=card-none>Pirate Ship</span>.
... attacking the other players.
... (Stiv reshuffles.)
... Stiv reveals a <span class=card-duration>Wharf</span> and a <span class=card
-treasure>Copper</span>.
... Luana trashes Stiv's <span class=card-treasure>Copper</span>.
... Luana gains a <span class=card-none>Pirate Ship</span> token.
Luana plays 2 <span class=card-treasure>Coppers</span>.
<span class=logonly>(Luana draws: 2 <span class=card-treasure>Silvers</span> and 3 <span class=card-treasure>Coppers</span>.)</span>
""")
        self.assertEquals(turn_info['name'], 'Luana')
        self.assertTrue('gains' not in turn_info)
        self.assertEquals(turn_info['money'], 2)

    def testBankTurn(self):
        turn_info = parse_game.ParseTurn(u"""
--- Maculus's turn 10 ---
Maculus plays a <span class=card-treasure>Silver</span>, 2 <span class=card-treasure>Coppers</span>, and a <span class=card-treasure>Gold</span>.
Maculus plays a <span class=card-treasure>Bank</span>.
... which is worth +$5.
Maculus buys a <span class=card-victory>Province</span>.
<span class=logonly>(Maculus draws: an <span class=card-victory>Estate</span>, a <span class=card-none>Bridge</span>, 2 <span class=card-treasure>Coppers</span>, and a <span class=card-treasure>Silver</span>.)</span>""")
        self.assertEquals(turn_info['money'], 12)

    def testPhilospherStoneTurn(self):
        turn_info = parse_game.ParseTurn(u"""
--- MonkeyBrains's turn 15 ---
MonkeyBrains plays a <span class=card-none>Laboratory</span>.
... drawing 2 cards and getting +1 action.
MonkeyBrains plays a <span class=card-none>Laboratory</span>.
... drawing 2 cards and getting +1 action.
MonkeyBrains plays a <span class=card-none>University</span>.
... getting +2 actions.
... gaining a <span class=card-none>Laboratory</span>.
MonkeyBrains plays an <span class=card-none>Herbalist</span>.
... getting +1 buy and +$1.
MonkeyBrains plays a <span class=card-treasure>Silver</span>.
MonkeyBrains plays a <span class=card-treasure>Copper</span>.
MonkeyBrains plays a <span class=card-treasure>Copper</span>.
MonkeyBrains plays a <span class=card-treasure>Copper</span>.
MonkeyBrains plays a <span class=card-treasure>Philosopher's Stone</span>.
... which is worth +$4 (6 cards in deck, 17 cards in discard).
MonkeyBrains buys a <span class=card-none>Laboratory</span>.
MonkeyBrains buys a <span class=card-none>Minion</span>.
MonkeyBrains returns a <span class=card-treasure>Philosopher's Stone</span> to the top of the deck.
<span class=logonly>(MonkeyBrains draws: an <span class=card-victory>Estate</span>, 2 <span class=card-none>Universities</span>, a <span class=card-treasure>Philosopher's Stone</span>, and a <span class=card-treasure>Potion</span>.)</span>""")
        self.assertEquals(turn_info['money'], 10)

    def testGainViaWorkshopTurn(self):
        turn_info = parse_game.ParseTurn(u"""
--- Stuart's turn 4 ---
Stuart plays a <span class=card-none>Workshop</span>.
... gaining a <span class=card-none>Bridge</span>.
Stuart plays 2 <span class=card-treasure>Coppers</span>.
Stuart buys a <span class=card-none>Pawn</span>.
(Stuart reshuffles.)
<span class=logonly>(Stuart draws: 4 <span class=card-treasure>Coppers</span> and a <span class=card-none>Pawn</span>.)</span>
""")
        self.assertEquals(turn_info['plays'], ['Workshop', 'Copper', 'Copper'])
        self.assertEquals(turn_info['gains'], ['Bridge'])
        self.assertEquals(turn_info['buys'], ['Pawn'])
        self.assertEquals(turn_info['money'], 2)
        
    def testWitchTurn(self):
        turn_info = parse_game.ParseTurn(u"""
--- FlippinPancakes's turn 5 ---
FlippinPancakes plays a <span class=card-none>Witch</span>.
... drawing 2 cards.
... Btnirn gains a <span class=card-curse>Curse</span>.
FlippinPancakes plays 2 <span class=card-treasure>Coppers</span>.
FlippinPancakes buys a <span class=card-duration>Lighthouse</span>.
<span class=logonly>(FlippinPancakes draws: 4 <span class=card-treasure>Coppers</span> and a <span class=card-none>Mining Village</span>.)</span>
""")
        self.assertEquals(turn_info['plays'], ['Witch', 'Copper', 'Copper'])
        self.assertTrue('gains' not in turn_info)
        self.assertEquals(turn_info['opp']['Btnirn']['gains'], ['Curse'])
        self.assertEquals(turn_info['money'], 2)

    def testSwindlerTurn(self):
        turn_info = parse_game.ParseTurn(u"""--- toaster's turn 9 ---
   toaster plays a <span class=card-none>Swindler</span>.
   ... getting +$2.
   ... brst13 turns up a <span class=card-treasure>Silver</span> and trashes it.
   ... replacing brst13's <span class=card-treasure>Silver</span> with a <span class=card-none>Shanty Town</span>.
   ... z666 turns up a <span class=card-none>Shanty Town</span> and trashes it.
   ... replacing z666's <span class=card-none>Shanty Town</span> with a <span class=card-none>Shanty Town</span>.""")
        self.assertEquals(turn_info['opp']['brst13']['gains'], ['Shanty Town'])
        self.assertEquals(turn_info['opp']['brst13']['trashes'], ['Silver'])
        self.assertEquals(turn_info['opp']['z666']['gains'], ['Shanty Town'])
        self.assertEquals(turn_info['opp']['z666']['trashes'], ['Shanty Town'])

    def testSaboteurTurn(self):
        turn_info = parse_game.ParseTurn(u"""--- BarneyRabble's turn 7 ---
BarneyRabble plays an <span class=card-none>Ironworks</span>.
... gaining an <span class=card-victory-action>Island</span>.
... (BarneyRabble reshuffles.)
... drawing 1 card and getting +1 action.
BarneyRabble plays a <span class=card-none>Saboteur</span>.
... Titandrake reveals an <span class=card-victory>Estate</span> and a <span class=card-treasure>Copper</span> and then a <span class=card-none>Baron</span>.
... The <span class=card-none>Baron</span> is trashed.
... Titandrake gains nothing to replace it.
... UfoSalata reveals a <span class=card-none>Baron</span> and trashes it.
... UfoSalata gains nothing to replace it.""")
        self.assertEquals(turn_info['opp']['Titandrake']['trashes'], ['Baron'])
        self.assertEquals(turn_info['opp']['UfoSalata']['trashes'], ['Baron'])

    def testSaboteurTurn2(self):
        turn_info = parse_game.ParseTurn("""--- UfoSalata's turn 14 ---
      UfoSalata plays a <span class=card-none>Saboteur</span>.
      ... BarneyRabble reveals a <span class=card-none>Saboteur</span> and trashes it.
      ... BarneyRabble gains a <span class=card-treasure>Silver</span> to replace it.
      ... Titandrake reveals 3 <span class=card-treasure>Coppers</span> and then an <span class=card-victory-action>Island</span>.
      ... The <span class=card-victory-action>Island</span> is trashed.
      ... Titandrake gains nothing to replace it.
      UfoSalata plays a <span class=card-treasure>Silver</span> and 3 <span class=card-treasure>Coppers</span>.
      UfoSalata buys a <span class=card-none>Saboteur</span>.
      <span class=logonly>(UfoSalata draws: a <span class=card-none>King's Court</span>, an <span class=card-victory>Estate</span>, a <span class=card-treasure>Silver</span>, an <span class=card-victory-action>Island</span>, and a <span class=card-treasure>Copper</span>.)</span> """)
        self.assertEquals(turn_info['opp']['BarneyRabble']['trashes'], 
                          ['Saboteur'])
        self.assertEquals(turn_info['opp']['BarneyRabble']['gains'], 
                          ['Silver'])
        self.assertEquals(turn_info['opp']['Titandrake']['trashes'], 
                          ['Island'])


    def testLookoutTurn(self):
        turn_info = parse_game.ParseTurn("""--- toaster's turn 9 ---
           toaster plays a <span class=card-none>Lookout</span>.
   ... getting +1 action.
   ... (toaster reshuffles.)
   ... drawing 3 cards.
   ... trashing a <span class=card-treasure>Copper</span>.
   ... discarding a <span class=card-treasure>Copper</span>.
   ... putting a card back on the deck.""")
        self.assertEquals(turn_info['trashes'], ['Copper'])

    def testCoppersmith(self):
        turn_info = parse_game.ParseTurn(u"""--- Alenia's turn 3 ---
Alenia plays a <span class=card-none>Coppersmith</span>.
... making each <span class=card-treasure>Copper</span> worth $2.
Alenia plays a <span class=card-treasure>Silver</span> and 2 <span class=card-treasure>Coppers</span>.
Alenia buys a <span class=card-victory-action>Nobles</span>.
<span class=logonly>(Alenia draws: 2 <span class=card-victory>Estates</span> and 3 <span class=card-treasure>Coppers</span>.)</span>""")
        self.assertEquals(turn_info['name'], 'Alenia')
        self.assertEquals(turn_info['plays'],
                          ['Coppersmith', 'Silver', 'Copper', 'Copper'])
        self.assertEquals(turn_info['number'], 3)
        self.assertEquals(turn_info['money'], 6)

    def testUTF8Name(self):
        turn_info = parse_game.ParseTurn(u"""--- Görling's turn 1 ---
Görling plays 3 <span class=card-treasure>Coppers</span>.
Görling buys a <span class=card-none>Workshop</span>.
<span class=logonly>(Görling draws: an <span class=card-victory>Estate</span> and 4 <span class=card-treasure>Coppers</span>.)</span> """)
        self.assertEquals(turn_info['name'], u'Görling')
        self.assertEquals(turn_info['money'], 3)

class ParseTurnsTest(unittest.TestCase):
    def testSimpleInput(self):
        turns_info = parse_game.ParseTurns(u"""
--- Zor Prime's turn 1 ---
Zor Prime plays 3 <span class=card-treasure>Coppers</span>.
Zor Prime buys a <span class=card-treasure>Silver</span>.
<span class=logonly>(Zor Prime draws: an <span class=card-victory>Estate</span> and 4 <span class=card-treasure>Coppers</span>.)</span>

   --- Andy's turn 1 ---
   Andy plays 5 <span class=card-treasure>Coppers</span>.
   Andy buys a <span class=card-none>Festival</span>.
   <span class=logonly>(Andy draws: 3 <span class=card-victory>Estates</span> and 2 <span class=card-treasure>Coppers</span>.)</span>

--- Zor Prime's turn 2 ---
Zor Prime plays 4 <span class=card-treasure>Coppers</span>.
Zor Prime buys a <span class=card-treasure>Silver</span>.
(Zor Prime reshuffles.)
<span class=logonly>(Zor Prime draws: an <span class=card-victory>Estate</span>, 2 <span class=card-treasure>Silvers</span>, and 2 <span class=card-treasure>Coppers</span>.)</span>
""")
        turn1Z = turns_info[0]
        self.assertEquals(turn1Z['name'], 'Zor Prime')
        self.assertEquals(turn1Z['plays'], ['Copper'] * 3)
        self.assertEquals(turn1Z['buys'], ['Silver'])

        turn1A = turns_info[1]
        self.assertEquals(turn1A['name'], 'Andy')
        self.assertEquals(turn1A['plays'], ['Copper'] * 5)
        self.assertEquals(turn1A['buys'], ['Festival'])

        turn2Z = turns_info[2]
        self.assertEquals(turn2Z['name'], 'Zor Prime')
        self.assertEquals(turn2Z['plays'], ['Copper'] * 4)
        self.assertEquals(turn2Z['buys'], ['Silver'])

class ParseDeckTest(unittest.TestCase):
    def testDeck(self):
        parsed_deck = parse_game.ParseDeck(u"""<b>Snead: 75 points</b> (7 <span class=card-victory>Colonies</span>, 2 <span class=card-victory-action>Islands</span>, and an <span class=card-victory>Estate</span>); 22 turns
       opening: <span class=card-victory-action>Island</span> / <span class=card-treasure>Silver</span>
       [15 cards] 2 <span class=card-victory-action>Islands</span>, 1 <span class=card-none>Chapel</span>, 1 <span class=card-duration>Tactician</span>, 1 <span class=card-treasure>Silver</span>, 2 <span class=card-treasure>Platinums</span>, 1 <span class=card-victory>Estate</span>, 7 <span class=card-victory>Colonies</span>""")
        self.assertEquals(parsed_deck['name'], 'Snead')
        self.assertEquals(parsed_deck['points'], 75)
        self.assertEquals(parsed_deck['vp_tokens'], 0)
        self.assertEquals(parsed_deck['deck'],
                          {'Island': 2,
                           'Chapel': 1,
                           'Tactician': 1,
                           'Silver': 1,
                           'Platinum': 2,
                           'Estate': 1,
                           'Colony': 7})

    def testDeckWithResign(self):
        parsed_deck = parse_game.ParseDeck(u"""<b>#1 kiwi</b>: resigned (1st); 13 turns
      opening: <span class=card-none>Shanty Town</span> / <span class=card-none>Baron</span> 
      [23 cards] 8 <span class=card-none>Shanty Towns</span>, 5 <span class=card-none>Rabbles</span>, 2 <span class=card-none>Expands</span>, 1 <span class=card-none>Market</span>, 6 <span class=card-treasure>Coppers</span>, 1 <span class=card-victory>Estate</span> """)
        self.assertEquals(parsed_deck['resigned'], True)

    def test20101213StyleDeck(self):
        parsed_deck = parse_game.ParseDeck(u"""<b>#1 zorkkorz</b>: 43 points (4 <span class=card-victory>Provinces</span>, 3 <span class=card-victory>Duchies</span>, 2 <span class=card-victory>Dukes</span>, and 2 <span class=card-victory-treasure>Harems</span>); 21 turns
          opening: <span class=card-none>Upgrade</span> / <span class=card-duration>Lighthouse</span> 
          [25 cards] 2 <span class=card-victory>Dukes</span>, 2 <span class=card-victory-treasure>Harems</span>, 2 <span class=card-none>Upgrades</span>, 1 <span class=card-none>Expand</span>, 1 <span class=card-duration>Lighthouse</span>, 4 <span class=card-treasure>Silvers</span>, 6 <span class=card-treasure>Golds</span>, 3 <span class=card-victory>Duchies</span>, 4 <span class=card-victory>Provinces</span> """)
        self.assertEquals(parsed_deck['name'], 'zorkkorz')

    def test20101213StyleDeckWithParenName(self):
        parsed_deck = parse_game.ParseDeck(u"""<b>#1 Foo (Bar)</b>: 43 points (4 <span class=card-victory>Provinces</span>, 3 <span class=card-victory>Duchies</span>, 2 <span class=card-victory>Dukes</span>, and 2 <span class=card-victory-treasure>Harems</span>); 21 turns
          opening: <span class=card-none>Upgrade</span> / <span class=card-duration>Lighthouse</span> 
          [25 cards] 2 <span class=card-victory>Dukes</span>, 2 <span class=card-victory-treasure>Harems</span>, 2 <span class=card-none>Upgrades</span>, 1 <span class=card-none>Expand</span>, 1 <span class=card-duration>Lighthouse</span>, 4 <span class=card-treasure>Silvers</span>, 6 <span class=card-treasure>Golds</span>, 3 <span class=card-victory>Duchies</span>, 4 <span class=card-victory>Provinces</span> """)
        self.assertEquals(parsed_deck['name'], 'Foo (Bar)')

    def test20101226EvilFingName(self):
        parsed_deck = parse_game.ParseDeck(u"""<b>#1 20 points</b>: 43 points (4 <span class=card-victory>Provinces</span>, 3 <span class=card-victory>Duchies</span>, 2 <span class=card-victory>Dukes</span>, and 2 <span class=card-victory-treasure>Harems</span>); 21 turns
          opening: <span class=card-none>Upgrade</span> / <span class=card-duration>Lighthouse</span> 
          [25 cards] 2 <span class=card-victory>Dukes</span>, 2 <span class=card-victory-treasure>Harems</span>, 2 <span class=card-none>Upgrades</span>, 1 <span class=card-none>Expand</span>, 1 <span class=card-duration>Lighthouse</span>, 4 <span class=card-treasure>Silvers</span>, 6 <span class=card-treasure>Golds</span>, 3 <span class=card-victory>Duchies</span>, 4 <span class=card-victory>Provinces</span> """)
        self.assertEquals(parsed_deck['name'], '20 points')
        self.assertEquals(parsed_deck['points'], 43)


    def testDeckWithVP(self):
        parsed_deck = parse_game.ParseDeck(u"""<b>Jon: 19 points</b> (16 ▼ and a <span class=card-victory>Duchy</span>); 20 turns
     opening: <span class=card-none>Salvager</span> / <span class=card-none>Black Market</span>
     [7 cards] 2 <span class=card-none>Bishops</span>, 1 <span class=card-duration>Tactician</span>, 1 <span class=card-treasure>Silver</span>, 2 <span class=card-treasure>Golds</span>, 1 <span class=card-victory>Duchy</span>""")
        self.assertEquals(parsed_deck['vp_tokens'], 16)

    def testDeckWithVP2(self):
        parsed_deck = parse_game.ParseDeck(u"""<b>Chrome: 12 points</b> (a <span class=card-victory>Province</span> and 6 ▼); 13 turns
        opening: <span class=card-none>Ironworks</span> / <span class=card-none>Black Market</span>
        [25 cards] 5 <span class=card-duration>Merchant Ships</span>, 5 <span class=card-none>Universities</span>, 2 <span class=card-none>Apprentices</span>, 2 <span class=card-none>Warehouses</span>, 1 <span class=card-none>Bishop</span>, 1 <span class=card-none>Black Market</span>, 1 <span class=card-none>Explorer</span>, 1 <span class=card-none>Worker's Village</span>, 6 <span class=card-treasure>Coppers</span>, 1 <span class=card-victory>Province</span>""")
        self.assertEquals(parsed_deck['vp_tokens'], 6)

    def testParseOldDeckWithParen(self):
        parsed_deck = parse_game.ParseDeck(u"""<b>Jeremy (BaconSnake): 66 points</b> (8 <span class=card-victory>Provinces</span>, 4 <span class=card-victory>Duchies</span>, and 6 <span class=card-victory>Estates</span>); 28 turns
                     opening: <span class=card-none>Smithy</span> / <span class=card-treasure>Silver</span> 
                     [38 cards] 2 <span class=card-none>Smithies</span>, 7 <span class=card-treasure>Coppers</span>, 5 <span class=card-treasure>Silvers</span>, 6 <span class=card-treasure>Golds</span>, 6 <span class=card-victory>Estates</span>, 4 <span class=card-victory>Duchies</span>, 8 <span class=card-victory>Provinces</span> """)
        self.assertEquals(parsed_deck['name'], 'Jeremy (BaconSnake)')

    def testDeckWithVP3(self):
        parsed_deck = parse_game.ParseDeck(u"""<b>Chrome: 12 points</b> (a <span class=card-victory>Province</span> and 26 ▼); 13 turns
        opening: <span class=card-none>Ironworks</span> / <span class=card-none>Black Market</span>
        [25 cards] 5 <span class=card-duration>Merchant Ships</span>, 5 <span class=card-none>Universities</span>, 2 <span class=card-none>Apprentices</span>, 2 <span class=card-none>Warehouses</span>, 1 <span class=card-none>Bishop</span>, 1 <span class=card-none>Black Market</span>, 1 <span class=card-none>Explorer</span>, 1 <span class=card-none>Worker's Village</span>, 6 <span class=card-treasure>Coppers</span>, 1 <span class=card-victory>Province</span>""")
        self.assertEquals(parsed_deck['vp_tokens'], 26)

    def testParseEmptyDeck(self):
        # it's random BS like this that makes writing a dominion log parser
        # a pain.
        parsed_deck = parse_game.ParseDeck(u"""<b>torchrat: 0 points</b> (nothing); 24 turns
          opening: <span class=card-none>Moneylender</span> / <span class=card-treasure>Silver</span>
          [0 cards] """)
        self.assertEquals(parsed_deck['vp_tokens'], 0)
        self.assertEquals(parsed_deck['deck'], {})

class AssignWinPointsTest(unittest.TestCase):
    def testAssignWinPointsSimple(self):
        g = {'decks': [
                {'points': 2, 'turns': [None, None]},
                {'points': 1, 'turns': [None, None]}
                ]}
        parse_game.AssignWinPoints(g)
        self.assertEquals(g['decks'][0]['win_points'], 2.0)
        self.assertEquals(g['decks'][1]['win_points'], 0.0)

    def testAssignWinPointsBreakTiesByTurns(self):
        g = {'decks': [
                {'points': 2, 'turns': [None, None]},
                {'points': 2, 'turns': [None]}
                ]}
        parse_game.AssignWinPoints(g)
        self.assertEquals(g['decks'][0]['win_points'], 0.0)
        self.assertEquals(g['decks'][1]['win_points'], 2.0)        
        
    def testTie(self):
        g = {'decks': [
                {'points': 2, 'turns': [None, None]},
                {'points': 2, 'turns': [None, None]}
                ]}
        parse_game.AssignWinPoints(g)        
        self.assertEquals(g['decks'][0]['win_points'], 1.0)
        self.assertEquals(g['decks'][1]['win_points'], 1.0)

    def testPartialTie(self):
        g = {'decks': [
                {'points': 2, 'turns': [None, None]},
                {'points': 2, 'turns': [None, None]},
                {'points': 1, 'turns': [None, None]}
                ]}
        parse_game.AssignWinPoints(g)        
        self.assertEquals(g['decks'][0]['win_points'], 1.5)
        self.assertEquals(g['decks'][1]['win_points'], 1.5)

class ParseGameHeaderTest(unittest.TestCase):
    def testParseHeader(self):
        parsed_header = parse_game.ParseHeader(u"""<html><head><link rel="stylesheet" href="/dom/client.css"><title>Dominion Game #2051</title></head><body><pre>AndMyAxe! wins!
All <span class=card-victory>Provinces</span> are gone.

cards in supply: <span cardname="Black Market" class=card-none>Black Market</span>, <span cardname="Caravan" class=card-duration>Caravan</span>, <span cardname="Chancellor" class=card-none>Chancellor</span>, <span cardname="City" class=card-none>City</span>, <span cardname="Council Room" class=card-none>Council Room</span>, <span cardname="Counting House" class=card-none>Counting House</span>, <span cardname="Explorer" class=card-none>Explorer</span>, <span cardname="Market" class=card-none>Market</span>, <span cardname="Mine" class=card-none>Mine</span>, and <span cardname="Pawn" class=card-none>Pawn</span>""")
        self.assertEquals(parsed_header['game_end'], ['Province'])
        self.assertEquals(parsed_header['supply'], ['Black Market',
                                                    "Caravan",
                                                    "Chancellor",
                                                    "City",
                                                    "Council Room",
                                                    "Counting House",
                                                    "Explorer",
                                                    "Market",
                                                    "Mine",
                                                    "Pawn"])

    def testHeaderWithResign(self):
        parsed_header = parse_game.ParseHeader(u"""<html><head><link rel="stylesheet" href="/client.css"><title>Dominion Game #262</title></head><body><pre>uberme wins!
All but one player has resigned.
 
cards in supply: <span cardname="Bank" class=card-treasure>Bank</span>, <span cardname="Black Market" class=card-none>Black Market</span>, <span cardname="Colony" class=card-victory>Colony</span>, <span cardname="Hoard" class=card-treasure>Hoard</span>, <span cardname="Ironworks" class=card-none>Ironworks</span>, <span cardname="Militia" class=card-none>Militia</span>, <span cardname="Moneylender" class=card-none>Moneylender</span>, <span cardname="Platinum" class=card-treasure>Platinum</span>, <span cardname="Rabble" class=card-none>Rabble</span>, <span cardname="Scout" class=card-none>Scout</span>, <span cardname="Sea Hag" class=card-none>Sea Hag</span>, and <span cardname="Worker's Village" class=card-none>Worker's Village</span>
""")
        self.assertEquals(parsed_header['game_end'], [])
        self.assertEquals(parsed_header['resigned'], True)
        

    def testParseHeaderWithMultiEnd(self):
        parsed_header = parse_game.ParseHeader(u"""<html><head><link rel="stylesheet" href="/dom/client.css"><title>Dominion Game #3865</title></head><body><pre>stormybriggs wins!
<span class=card-victory>Duchies</span>, <span class=card-victory>Estates</span>, and <span class=card-none>Peddlers</span> are all gone.

cards in supply: <span cardname="Colony" class=card-victory>Colony</span>, <span cardname="Grand Market" class=card-none>Grand Market</span>, <span cardname="Loan" class=card-treasure>Loan</span>, <span cardname="Mine" class=card-none>Mine</span>, <span cardname="Monument" class=card-none>Monument</span>, <span cardname="Outpost" class=card-duration>Outpost</span>, <span cardname="Peddler" class=card-none>Peddler</span>, <span cardname="Platinum" class=card-treasure>Platinum</span>, <span cardname="Stash" class=card-treasure>Stash</span>, <span cardname="Warehouse" class=card-none>Warehouse</span>, <span cardname="Witch" class=card-none>Witch</span>, and <span cardname="Worker's Village" class=card-none>Worker's Village</span>
""")
        self.assertEquals(parsed_header['game_end'], ['Duchy', 'Estate', 
                                                      'Peddler'])
        self.assertEquals(parsed_header['resigned'], False)

class ValidateNamesTest(unittest.TestCase):
    def testKeywordInName(self):
        decks = [{'name': 'gains a curse'}]
        self.assertRaises(parse_game.BogusGame, parse_game.ValidateNames, decks)

    def testStartsWithPeriod(self):
        decks = [{'name': '.evil'}]
        self.assertRaises(parse_game.BogusGame, parse_game.ValidateNames, decks)

class ParseGameTest(unittest.TestCase):
    def testParseGame(self):
        parsed_game = parse_game.ParseGame(u"""<html><head><link rel="stylesheet" href="/dom/client.css"><title>Dominion Game #2083</title></head><body><pre>Alenia wins!
All <span class=card-victory>Provinces</span> are gone.

cards in supply: <span cardname="Coppersmith" class=card-none>Coppersmith</span>, <span cardname="Expand" class=card-none>Expand</span>, <span cardname="Gardens" class=card-victory>Gardens</span>, <span cardname="Mining Village" class=card-none>Mining Village</span>, <span cardname="Nobles" class=card-victory-action>Nobles</span>, <span cardname="Outpost" class=card-duration>Outpost</span>, <span cardname="Pearl Diver" class=card-none>Pearl Diver</span>, <span cardname="Thief" class=card-none>Thief</span>, <span cardname="Throne Room" class=card-none>Throne Room</span>, and <span cardname="Worker's Village" class=card-none>Worker's Village</span>

----------------------

<b>Alenia: 58 points</b> (8 <span class=card-victory>Provinces</span> and 5 <span class=card-victory-action>Nobles</span>); 24 turns
        opening: <span class=card-treasure>Silver</span> / <span class=card-none>Coppersmith</span>
        [37 cards] 5 <span class=card-victory-action>Nobles</span>, 3 <span class=card-none>Expands</span>, 3 <span class=card-none>Pearl Divers</span>, 3 <span class=card-none>Worker's Villages</span>, 1 <span class=card-duration>Outpost</span>, 1 <span class=card-none>Throne Room</span>, 5 <span class=card-treasure>Coppers</span>, 8 <span class=card-treasure>Silvers</span>, 8 <span class=card-victory>Provinces</span>

<b>AndMyAxe!: 30 points</b> (5 <span class=card-victory>Gardens</span> [46 cards], 7 <span class=card-victory>Estates</span>, and a <span class=card-victory>Duchy</span>); 23 turns
           opening: <span class=card-treasure>Silver</span> / <span class=card-none>Worker's Village</span>
           [46 cards] 6 <span class=card-none>Worker's Villages</span>, 5 <span class=card-victory>Gardens</span>, 1 <span class=card-none>Coppersmith</span>, 1 <span class=card-duration>Outpost</span>, 1 <span class=card-none>Throne Room</span>, 21 <span class=card-treasure>Coppers</span>, 3 <span class=card-treasure>Silvers</span>, 7 <span class=card-victory>Estates</span>, 1 <span class=card-victory>Duchy</span>

----------------------

trash: a <span class=card-treasure>Silver</span>, 3 <span class=card-victory>Gardens</span>, a <span class=card-victory>Duchy</span>, 3 <span class=card-victory>Estates</span>, 2 <span class=card-treasure>Coppers</span>, a <span class=card-none>Coppersmith</span>, and 3 <span class=card-none>Expands</span>
league game: no

<hr/><b>Game log</b>

Turn order is Alenia and then AndMyAxe!.

<span class=logonly>(Alenia's first hand: 2 <span class=card-victory>Estates</span> and 3 <span class=card-treasure>Coppers</span>.)</span>
<span class=logonly>(AndMyAxe!'s first hand: 2 <span class=card-victory>Estates</span> and 3 <span class=card-treasure>Coppers</span>.)</span>

--- Alenia's turn 1 ---
Alenia plays 3 <span class=card-treasure>Coppers</span>.
Alenia buys a <span class=card-treasure>Silver</span>.
<span class=logonly>(Alenia draws: an <span class=card-victory>Estate</span> and 4 <span class=card-treasure>Coppers</span>.)</span>

   --- AndMyAxe!'s turn 1 ---
   AndMyAxe! plays 3 <span class=card-treasure>Coppers</span>.
   AndMyAxe! buys a <span class=card-treasure>Silver</span>.
   <span class=logonly>(AndMyAxe! draws: an <span class=card-victory>Estate</span> and 4 <span class=card-treasure>Coppers</span>.)</span>

--- Alenia's turn 2 ---
Alenia plays 4 <span class=card-treasure>Coppers</span>.
Alenia buys a <span class=card-none>Coppersmith</span>.
(Alenia reshuffles.)
<span class=logonly>(Alenia draws: an <span class=card-victory>Estate</span>, a <span class=card-treasure>Silver</span>, 2 <span class=card-treasure>Coppers</span>, and a <span class=card-none>Coppersmith</span>.)</span>

   --- AndMyAxe!'s turn 2 ---
   AndMyAxe! plays 4 <span class=card-treasure>Coppers</span>.
   AndMyAxe! buys a <span class=card-none>Worker's Village</span>.
   (AndMyAxe! reshuffles.)
   <span class=logonly>(AndMyAxe! draws: 2 <span class=card-victory>Estates</span> and 3 <span class=card-treasure>Coppers</span>.)</span>

--- Alenia's turn 3 ---
Alenia plays a <span class=card-none>Coppersmith</span>.
... making each <span class=card-treasure>Copper</span> worth $2.
Alenia plays a <span class=card-treasure>Silver</span> and 2 <span class=card-treasure>Coppers</span>.
Alenia buys a <span class=card-victory-action>Nobles</span>.
<span class=logonly>(Alenia draws: 2 <span class=card-victory>Estates</span> and 3 <span class=card-treasure>Coppers</span>.)</span>

All <span class=card-victory>Provinces</span> are gone.
Alenia wins!
</pre></body></html>""")
        self.assertEquals(parsed_game['players'], ['alenia', 'andmyaxe!'])
        self.assertEquals(parsed_game['decks'][0]['name'], 'Alenia')
        self.assertEquals(parsed_game['decks'][0]['points'], 58)
        self.assertEquals(parsed_game['decks'][0]['order'], 1)
        self.assertEquals(parsed_game['decks'][1]['name'], 'AndMyAxe!')
        self.assertEquals(parsed_game['decks'][1]['order'], 2)
        self.assertEquals(len(parsed_game['decks'][0]['turns']), 3)
        self.assertEquals(len(parsed_game['decks'][1]['turns']), 2)
        
        self.assertEquals(parsed_game['decks'][0]['win_points'], 2.0)
        self.assertEquals(parsed_game['decks'][1]['win_points'], 0.0)

        self.assertEquals(parsed_game['decks'][0]['turns'][2]['plays'], 
                          ['Coppersmith', 'Silver', 'Copper', 'Copper'])
        self.assertEquals(parsed_game['supply'],
                          ["Coppersmith", 
                           "Expand",
                           "Gardens",
                           "Mining Village",
                           "Nobles",
                           "Outpost",
                           "Pearl Diver",
                           "Thief", 
                           "Throne Room",
                           "Worker's Village"])

    EVIL_GAME_CONTENTS = u"""<html><head><link rel="stylesheet" href="/client.css"><title>Dominion Game #40068</title></head><body><pre>dcg wins!
All but one player has resigned.

cards in supply: <span cardname="Apprentice" class=card-none>Apprentice</span>, <span cardname="Familiar" class=card-none>Familiar</span>, <span cardname="Island" class=card-victory-action>Island</span>, <span cardname="Minion" class=card-none>Minion</span>, <span cardname="Possession" class=card-none>Possession</span>, <span cardname="Potion" class=card-treasure>Potion</span>, <span cardname="Royal Seal" class=card-treasure>Royal Seal</span>, <span cardname="Shanty Town" class=card-none>Shanty Town</span>, <span cardname="Throne Room" class=card-none>Throne Room</span>, <span cardname="Trade Route" class=card-none>Trade Route</span>, and <span cardname="Upgrade" class=card-none>Upgrade</span>

----------------------

<b>#1 dcg</b>: 3 points (3 <span class=card-victory>Estates</span>); 1 turns
     opening: <span class=card-treasure>Potion</span> / nothing
     [11 cards] 7 <span class=card-treasure>Coppers</span>, 1 <span class=card-treasure>Potion</span>, 3 <span class=card-victory>Estates</span>

<b>#2 8----------------------D</b>: resigned (1st); 2 turns
                          opening: <span class=card-none>Minion</span> / nothing
                          [11 cards] 1 <span class=card-none>Minion</span>, 7 <span class=card-treasure>Coppers</span>, 3 <span class=card-victory>Estates</span>

----------------------

trash: nothing
league game: no

<hr/><b>Game log</b>

Turn order is 8----------------------D and then dcg.

<span class=logonly>(8----------------------D's first hand: 5 <span class=card-treasure>Coppers</span>.)</span>
<span class=logonly>(dcg's first hand: an <span class=card-victory>Estate</span> and 4 <span class=card-treasure>Coppers</span>.)</span>

--- 8----------------------D's turn 1 ---
8----------------------D plays 5 <span class=card-treasure>Coppers</span>.
8----------------------D buys a <span class=card-none>Minion</span>.
<span class=logonly>(8----------------------D draws: 3 <span class=card-victory>Estates</span> and 2 <span class=card-treasure>Coppers</span>.)</span>

   --- dcg's turn 1 ---
   dcg plays 4 <span class=card-treasure>Coppers</span>.
   dcg buys a <span class=card-treasure>Potion</span>.
   <span class=logonly>(dcg draws: 2 <span class=card-victory>Estates</span> and 3 <span class=card-treasure>Coppers</span>.)</span>

--- 8----------------------D's turn 2 ---
8----------------------D resigns from the game (client disconnected).

All but one player has resigned.
dcg wins!
</pre></body></html>"""
    def testParseGameWithEvilName(self):
        parsed_game = parse_game.ParseGame(ParseGameTest.EVIL_GAME_CONTENTS)
        self.assertEquals(parsed_game['players'], ['8----------------------d',
                                                   'dcg'])

    def testParseGameWithBogusCheck(self):
        self.assertRaises(parse_game.BogusGame, parse_game.ParseGame, 
                          ParseGameTest.EVIL_GAME_CONTENTS, True)

    def testParseGameWithReverseTurnOrder(self):
        parsed_game = parse_game.ParseGame(ParseGameTest.EVIL_GAME_CONTENTS)
        self.assertEquals(parsed_game['decks'][0]['order'], 2)
        self.assertEquals(parsed_game['decks'][1]['order'], 1)


if __name__ == '__main__':
    unittest.main()
