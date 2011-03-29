#!/usr/bin/python
# -*- coding: utf-8 -*-
import collections
import codecs
import copy
import gzip
import os
import multiprocessing
import re
import sys

import card_info
import game
import utils
import name_merger
from game import Game

import simplejson as json


SECTION_SEP = re.compile('^----------------------$', re.MULTILINE)
TURN_HEADER_RE = re.compile("--- (?P<name>.+)'s turn (?P<turn_no>\d+) ---")
TURN_HEADER_NO_GROUP_RE = re.compile("--- .+'s turn \d+ ---")
SPLIT_COMMA_AND_RE = re.compile(',| and ')
NUMBER_BEFORE_SPAN = re.compile('(\d+) <span')
NAME_BEFORE_GAINS = re.compile('\.\.\. (.)* gains a')
NUMBER_COPIES = re.compile('(0|2) copies to')
GETTING_MONEY_RE = re.compile(' \+\$(\d)+')
WHICH_IS_WORTH_RE = re.compile(' which is worth \+\$(\d)+')


KW_TRASHING = ' trashing '
KW_TRASHES = ' trashes ' 
KW_IS_TRASHED = ' is trashed.'
KW_GAINING = ' gaining ' 
KW_PLAYS = ' plays ' 
KW_BUYS = ' buys '
KW_GAINS_A = ' gains a'
KW_TOKEN = ' token.'
KW_DISCARDS = ' discards '
KW_REVEALS = ' reveals '
KW_RETURNING = ' returning ' 
KW_REVEALING = ' revealing '
KW_TO_THE_SUPPLY = ' to the supply'
KW_GETTING = ' getting +'
KW_WHICH_IS_WORTH = ' which is worth +$'
KW_TURNS_UP_A = ' turns up a'
KW_REVEALS_A = ' reveals a'
KW_REPLACING = ' replacing '
KW_WITH_A = ' with a '
KW_TRASHES_IT = 'trashes it.'

KEYWORDS = [locals()[w] for w in dict(locals()) if w.startswith('KW_')]

class BogusGame:
    def __init__(self, reason):
        self.reason = reason

def CaptureCards(line):
    def AsIntOr1(s):
        try:
            return int(s)
        except ValueError:
            return 1

    cards = []
    card_sections = SPLIT_COMMA_AND_RE.split(line)
    for sect in card_sections:
        split_at_span = sect.split('<span')
        if len(split_at_span) == 0:
            continue
        first = split_at_span[0]
        split_first = first.split()
        if len(split_first) == 0:
            mult = 1
        else:
            mult = AsIntOr1(split_first[-1])

        for subsect in split_at_span:
            start_of_end_span = subsect.find('</span')
            if start_of_end_span == -1:
                continue
            end_of_begin_span = subsect.rfind('>', 0, start_of_end_span)
            if end_of_begin_span == -1:
                continue
            maybe_plural = subsect[end_of_begin_span + 1: 
                                   start_of_end_span]
            try:
                card = card_info.SingularOf(maybe_plural)
            except KeyError, e:
                print line
                raise e
            cards.extend([card] * mult)
    return cards    

def AssignWinPoints(game_dict):
    def WinTuple(deck_dict):        
        # negate turns so that max() behaves; points good, turns bad.
        return (deck_dict['points'], -len(deck_dict['turns']))

    decks = game_dict['decks']
    winner_tuple = max(WinTuple(p) for p in decks)
    winners = [p for p in decks if WinTuple(p) == winner_tuple]

    win_points = float(len(decks)) / len(winners)
    for p in decks:
        p['win_points'] = win_points if p in winners else 0.0

def IndexGameByNormPlayerName(game, turns):
    game['players'] = []
    for turn in turns:
        n = name_merger.NormName(turn['name'])
        if not n in game['players']:
            game['players'].append(n)

def AssociateTurnsWithOwner(game, turns):
    # In doing this, we can remove the names from the turns to save some space.
    name_to_owner = {}
    for d in game['decks']:
        name_to_owner[d['name']] = d
        d['turns'] = []

    order_ct = 0

    for idx, turn in enumerate(turns):
        owner = name_to_owner[turn['name']]
        owner['turns'].append(turn)
        if not 'order' in owner:
            owner['order'] = idx + 1
            order_ct += 1
        del turn['name']

    if order_ct != len(game['decks']):
        raise BogusGame('Did not find turns for all players')

def ValidateNames(decks):
    # Raise an exception for names that might screw up the parsing.  Hopefully
    # this will be less than 1% of games, but it's just easier to punt
    # on annoying inputs that to make sure we get them right.
    used_names = set()
    for deck in decks:
        name = deck['name']
        if name in used_names:
            raise BogusGame('Duplicate name %s' % name)
        used_names.add(name)

        if name[0] == '.':
            raise BogusGame('name %s starts with period' % name)
        for kw in KEYWORDS:
            if kw.lstrip() in name or kw.rstrip() in name:
                raise BogusGame('name %s contains keyword %s' % (name, kw))

    if len(used_names) != len(decks):
        raise BogusGame('not everyone took a turn?')
    if len(decks) <= 1:
        raise BogusGame('only one player')


def ParseGame(game_str, dubious_check = False):
    try:
        split_sects = SECTION_SEP.split(game_str)
        header_str, decks_blob, trash_and_turns = split_sects
        #decks_blob += '\n'
        #trash_and_turns += '\n'
    except ValueError, e:
        print len(split_sects), SECTION_SEP.split(game_str), game_str
        raise e
    trash_str, turns_str = trash_and_turns.split('Game log')
    turns_str = turns_str[turns_str.find('---'):]
    
    game = ParseHeader(header_str)
    decks = ParseDecks(decks_blob)
    game['decks'] = decks

    ValidateNames(decks)

    turns = ParseTurns(turns_str)
    
    IndexGameByNormPlayerName(game, turns)
    AssociateTurnsWithOwner(game, turns)
    AssignWinPoints(game)

    if dubious_check and Game(game).DubiousQuality():
        raise BogusGame('Dubious Quality')

    return game

def ParseHeader(header_str):
    sections = filter(None, 
                      header_str.replace(' \n', '\n').split('\n\n'))
    end_str, supply_str = sections
    assert 'gone' in end_str or 'resigned' in end_str
    if 'gone' in end_str:
        resigned = False
        gone = CaptureCards(end_str.split('\n')[1])
    else:
        resigned = True
        gone = []
    supply = CaptureCards(supply_str)
    return {'game_end': gone, 'supply': supply, 
            'resigned': resigned}

PLACEMENT_RE = re.compile('#\d (.*)')

def CleanupName(name):
    htmlless_name = name.replace('<b>', '').replace('</b>', '')
    placement_match = PLACEMENT_RE.match(htmlless_name)
    if placement_match:
        return placement_match.group(1)
    return htmlless_name

POINTS_RE = re.compile(': (-*\d+) points(\s|(\<\\/b\>))')

def ParseDeck(deck_str):
    name_vp_list, opening, deck_contents = deck_str.split('\n')
    vp_tokens = 0
    #print 'vp', name_vp_list

    matched_points = POINTS_RE.search(name_vp_list)
    
    if matched_points:
        point_loc = matched_points.end()
        resigned, points  = False, int(matched_points.group(1))
        name_points, vp_list = (name_vp_list[:point_loc], 
                                name_vp_list[point_loc + 1:])
    else:
        resign_loc = name_vp_list.find('resigned')
        assert resign_loc != -1
        resigned, points = True, -100
        name_points, vp_list = (name_vp_list[:resign_loc],
                                name_vp_list[resign_loc + 1:])

    last_colon_in_name_points = name_points.rfind(':')
    name, points_or_resign = (name_points[:last_colon_in_name_points],
                              name_points[last_colon_in_name_points + 1:])
    name = CleanupName(name)

    for chunk in vp_list.split(','):
        diamond_loc = chunk.find(u'▼')
        if diamond_loc != -1:
            start_point_loc = max(chunk.rfind('(', 0, diamond_loc - 1),
                                  chunk.rfind(' ', 0, diamond_loc - 1))
            vp_tokens = int(chunk[start_point_loc + 1:diamond_loc - 1])

        card_list_chunks = deck_contents[
            deck_contents.find(']') + 1:].replace(',', ' ')
        card_blobs = [x for x in card_list_chunks.split('</span>') if 
                      '<span' in x]
        deck_comp = {}
        for card_blob in card_blobs:
            right_bracket_index = card_blob.find('>')
            card_name = card_blob[right_bracket_index + 1:]
            try:
                card_name = card_info.SingularOf(card_name)
            except KeyError, e:
                print chunk, card_name, card_blob[right_bracket_index - 10:]
                raise e
            card_quant = int(card_blob.split()[0])
            deck_comp[card_name] = card_quant
    return {'name': name, 'points': points, 'resigned': resigned,
            'deck': deck_comp, 'vp_tokens': vp_tokens}

def ParseDecks(decks_blob):
    deck_blobs = filter(None, decks_blob.split('\n\n'))
    # print 'got %d deck blobs' % len(deck_blobs)
    return [ParseDeck(deck_blob) for deck_blob in deck_blobs]

def _StripLeading(s, dead_chars):
    for idx, c in enumerate(s):
        if c not in dead_chars:
            return s[idx:]
    return ''

def NameAndRest(line, term):
    start_of_term = line.find(term)
    assert start_of_term != -1
    # this is going to break on things names that actually start with a 
    # period, but I punted on those with a BogusGame anyway
    name = _StripLeading(line[:start_of_term], ' .').strip()
    return name, line[start_of_term + len(term):]

def _DeleteKeysWithEmptyVals(d):
    keys_to_die = []
    for k in d:
        if not d[k]:
            keys_to_die.append(k)
    for k in keys_to_die:
        del d[k]

def CountMoney(plays):
    coppersmith_ct = 0
    money = 0
    for card in plays:
        if card == 'Coppersmith':  
            coppersmith_ct += 1
        elif card == 'Copper':
            money += 1 + coppersmith_ct
        elif card_info.IsTreasure(card):
            money += card_info.MoneyValue(card)
    return money

def ParseTurn(turn_blob):
    lines = turn_blob.strip().split('\n')
    header = lines[0]
    parsed_header = TURN_HEADER_RE.search(header)
    if parsed_header:
        name = parsed_header.group('name')
        turn_no = int(parsed_header.group('turn_no'))
    else:
        raise ValueError("Could not parse header " + header)
    
    plays = []
    gains = []
    buys = []
    trashes = []
    returns = []
    turn_money = 0
    opp_turn_info = collections.defaultdict(lambda: {'gains': [],
                                                     'trashes': []})
    last_noted_player = None
    for line_idx, line in enumerate(lines):
        has_trashing = KW_TRASHING in line
        has_trashes = KW_TRASHES in line
        has_gaining = KW_GAINING in line
        if has_trashes:
            if has_gaining:
                # Trading post turn, first trashes, then gaining
                gain_start = line.find(KW_GAINING)
                trashes.extend(CaptureCards(line[:gain_start]))
                gains.extend(CaptureCards(line[gain_start:]))
                continue            
            if line.endswith(KW_TRASHES_IT):
                if KW_TURNS_UP_A in line:
                    # Swinder turn
                    last_noted_player, rest = NameAndRest(line, KW_TURNS_UP_A) 
                elif KW_REVEALS_A in line:
                    # Sab turn
                    last_noted_player, rest = NameAndRest(line, KW_REVEALS_A)
                else:
                    assert False, 'Did not handle trashing in line %s' % line 
                
                opp_turn_info[last_noted_player]['trashes'].extend(
                    CaptureCards(line))
        if KW_WITH_A in line:
            if KW_REPLACING in line:
                assert last_noted_player in line
                new_gained_portion = line[line.find(KW_WITH_A):]
                opp_turn_info[last_noted_player]['gains'].extend(CaptureCards(
                        new_gained_portion))
        if KW_PLAYS in line: plays.extend(CaptureCards(line))
        if has_gaining and not KW_TOKEN in line: 
            gains.extend(CaptureCards(line[line.find(KW_GAINING):])) 
        if KW_BUYS in line: buys.extend(CaptureCards(line))
        if has_trashing: trashes.extend(CaptureCards(line))
        if KW_GAINS_A in line and not KW_TOKEN in line:
            opp_name, rest = NameAndRest(line, KW_GAINS_A)
            if KW_DISCARDS in opp_name:  
                opp_name = opp_name[:opp_name.find(KW_DISCARDS)]
            opp_turn_info[opp_name]['gains'].extend(CaptureCards(rest))
        if KW_TRASHES in line:
            n, rest = NameAndRest(line, 'trashes')
            if n == name:
                trashes.extend(CaptureCards(rest))
            else:
                cards_opp_trashed = CaptureCards(rest)
                if cards_opp_trashed:
                    opp_turn_info[n]['trashes'].extend(cards_opp_trashed)
        if KW_IS_TRASHED in line:
            # Saboteur after revealing cards, name not mentioned on this line.
            assert last_noted_player != None, line
            cards = CaptureCards(line)
            opp_turn_info[last_noted_player]['trashes'].extend(cards)
        if KW_REVEALS in line:
            last_noted_player, rest = NameAndRest(line, KW_REVEALS)
            card_revealed = CaptureCards(line)

            # arg, ambassador requires looking at the next line to figure
            # out how many copies were returned
            if (card_revealed and line_idx + 1 < len(lines) and 
                KW_RETURNING in lines[line_idx + 1]):
                next_line = lines[line_idx + 1]
                num_copies = 1
                num_copies_match = NUMBER_COPIES.search(next_line)
                if num_copies_match:
                    num_copies = int(num_copies_match.group(1))
                returns.extend(card_revealed * num_copies)
        if KW_REVEALING in line and KW_TO_THE_SUPPLY in line:
            # old style ambassador line
            returns.extend(CaptureCards(line))
        if KW_GETTING in line:
            money_match = GETTING_MONEY_RE.search(line)
            if money_match:
                turn_money += int(money_match.group(1))
        if KW_WHICH_IS_WORTH in line:
            worth_match = WHICH_IS_WORTH_RE.search(line)
            assert bool(worth_match), line
            turn_money += int(worth_match.group(1))
            
    for opp in opp_turn_info:
        _DeleteKeysWithEmptyVals(opp_turn_info[opp])
    # TODO:  Consider getting rid of turn number from the DB?  It's easy
    # to recompute from the game state anyway, and it would save some space.
    ret = {'name': name, 'number': turn_no, 'plays': plays , 
           'buys': buys, 'gains': gains, 'trashes': trashes, 
           'returns': returns, 'money': CountMoney(plays) + turn_money,
           'opp': dict(opp_turn_info)}

    _DeleteKeysWithEmptyVals(ret)
    return ret

def ParseTurns(turns_blob):
    turns = []
    turn_blobs = TURN_HEADER_NO_GROUP_RE.split(turns_blob)
    if turn_blobs[0].strip() == '':
        turn_blobs = turn_blobs[1:]
    turn_headers = TURN_HEADER_NO_GROUP_RE.findall(turns_blob)
    for turn_header, turn_blob in zip(turn_headers, turn_blobs):
        turns.append(ParseTurn(turn_header + turn_blob))
    return turns

def OuterParseGame(fn):
    contents = codecs.open(fn, 'r', encoding='utf-8').read()
    if not contents:
        print 'empty game'
        return None
    if '<b>game aborted' in contents:
        print 'skipping aborted game', fn
        return None
    try:
        p = ParseGame(contents, dubious_check = True)
        p['_id'] = fn.split('/')[-1]
        return p
    except BogusGame, b:
        print 'skipped', fn, 'because', b.reason
        return None

# http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
def Segments(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def DumpSegment(arg_tuple):
    idx, year_month_day, segment = arg_tuple
    out_name = 'parsed_out/%s-%d.json' % (year_month_day, idx)
    json.dump(segment, open(out_name, 'w'), indent=2, sort_keys=True)

class Converter:
    def ConvertToJson(self, year_month_day, games_to_parse = None):
        if games_to_parse is None:
            games_to_parse = os.listdir('static/scrape_data/' + year_month_day)
            games_to_parse = ['static/scrape_data/' + year_month_day + '/' + g 
                              for g in games_to_parse if g.endswith('html')]

        if not games_to_parse:
            print 'no data files to parse in ', year_month_day
            return

        try:
            pool = multiprocessing.Pool()
            parsed_games = pool.map(OuterParseGame, games_to_parse, 
                                    chunksize=50)
            #parsed_games = map(OuterParseGame, games_to_parse)
            print year_month_day, 'before filtering', len(parsed_games)
            parsed_games = filter(None, parsed_games)
            print year_month_day, 'after filtering', len(parsed_games)
            game_segments = list(Segments(parsed_games, 100))
            labelled_segments = [(i, year_month_day, c) for i, c in
                               enumerate(game_segments)]
            pool.map(DumpSegment, labelled_segments)
        except int, e:
            print e, 'trouble parsing', fn
            raise e

def ParseGameFromFile(fn):
    contents = codecs.open(fn, 'r', encoding='utf-8').read()
    print ParseGame(contents, dubious_check = True)

def main():
    #fn = 'static/scrape_data/20110308/game-20110308-150636-a5444af5.html'
    #print AnnotateGame(codecs.open(fn, 'r', encoding='utf-8').read()).encode(
    #    'utf-8')
    #return
    args = utils.IncrementalDateRangeCmdLineParser().parse_args()
    print args
    days = os.listdir('static/scrape_data')
    days.sort()
    for year_month_day in days:
        if not utils.IncludesDay(args, year_month_day):
            print year_month_day, 'not in date range, skipping'
            continue
            
        if args.incremental and os.path.exists(
            'parsed_out/%s-0.json' % year_month_day):
            print 'skipping', year_month_day, 'because already done'
            continue        

        Converter().ConvertToJson(year_month_day)

def t():
    for year_month_day in os.listdir('static/scrape_data')[:1]:
        Converter().ConvertToJson(year_month_day)    

def AnnotateGame(contents):
    parsed_game = ParseGame(contents, dubious_check = False)
    states = []
    
    game_val = game.Game(parsed_game)
    for game_state in game_val.GameStateIterator():
        states.append(game_state.EncodeGameState())

    parsed_game['game_states'] = states

    ret = u''

    start_body = contents.find('<body>') + len('<body>')
    ret += contents[:start_body]
    ret += """
<div id="game-display"></div>
<script src="static/flot/jquery.js"></script>
<script src="static/game_viewer.js"></script>
<script type="text/javascript">
        var game = %s;
        var card_list = %s;
        $(document).ready(DecorateGame);
</script>
""" % (json.dumps(parsed_game, indent=2), 
       open('static/card_list.js', 'r').read())
    contents = contents[start_body:]
    
    while True:
        cur_match = TURN_HEADER_RE.search(contents)
        if cur_match:
            player = cur_match.group('name')
            turn_no = int(cur_match.group('turn_no')) - 1
            ret += contents[:cur_match.start()]
            # these turn id's are 0 indexed
            turn_id = '%s-turn-%d' % (player, turn_no)
            # and since these are shown, they are 1 indexed
            show_turn_id = '%s-show-turn-%d' % (player, turn_no + 1)
            ret += '<div id="%s"></div>' % turn_id
            ret += '<a name="%s"></a><a href="#%s">%s</a>' % (
                show_turn_id, show_turn_id, cur_match.group())
                
            contents = contents[cur_match.end():]
        else:
            break
    before_end = contents.find('</html')
    ret = ret + contents[:before_end]
    ret += '<div id="end-game">\n'
    ret += '</div>&nbsp<br>\n' * 10  
    contents = contents[before_end:]
    return ret + contents
    
def profilemain():
    import hotshot, hotshot.stats
    prof = hotshot.Profile("parse_game.prof")
    prof.runcall(t)
    prof.close()
    stats = hotshot.stats.load("parse_game.prof")
    stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(20)

if __name__ == '__main__':
    utils.ensure_exists('parsed_out')
    main()
    
