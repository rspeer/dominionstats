#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Parse raw game data from isotropic into JSON list of game documents."""

import collections
import codecs
import os
import multiprocessing
import pprint
import re

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
KW_GETS = ' gets +'
KW_WHICH_IS_WORTH = ' which is worth +$'
KW_TURNS_UP_A = ' turns up a'
KW_REVEALS_A = ' reveals a'
KW_REPLACING = ' replacing '
KW_WITH_A = ' with a '
KW_TRASHES_IT = 'trashes it.'
KEYWORDS = [locals()[w] for w in dict(locals()) if w.startswith('KW_')]

class BogusGame(Exception):
    """ Exception for a degenerate game that cannot or should not be parsed."""

    def __init__(self, reason):
        Exception.__init__(self)
        self.reason = reason

def capture_cards(line):
    """ Given a line of text from isotropic, extract the card names

    line: string like 'Rob plays a <span class=card-none>Minion</span>.'
    returns: list of string of card names, ['Minion']
    """
    def _as_int_or_1(string_val):
        try:
            return int(string_val)
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
            mult = _as_int_or_1(split_first[-1])

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
            except KeyError, exception:
                print line
                raise exception
            cards.extend([card] * mult)
    return cards    

def assign_win_points(game_dict):
    """ Set win_points to number of win points for each player in game_dict."""
    def win_tuple(deck_dict):        
        """ Return tuple that ordered by increasing final standing """
        # negate turns so that max() behaves; points good, turns bad.
        return (deck_dict['points'], -len(deck_dict['turns']))

    decks = game_dict['decks']
    winner_tuple = max(win_tuple(p) for p in decks)
    winners = [p for p in decks if win_tuple(p) == winner_tuple]

    win_points = float(len(decks)) / len(winners)
    for player in decks:
        player['win_points'] = win_points if player in winners else 0.0

def associate_game_with_norm_names(game_dict):
    """ Fill players field in game_dict with list of normed player names."""
    game_dict['players'] = []
    for player_deck in game_dict['decks']:
        normed_name = name_merger.NormName(player_deck['name'])
        game_dict['players'].append(normed_name)

def associate_turns_with_owner(game_dict, turns):
    """ Move each turn in turns to be a member of the corresponding player
    in game_dict.  We can remove the names from the turn."""
    name_to_owner = {}
    for idx, deck in enumerate(game_dict['decks']):
        name_to_owner[deck['name']] = deck
        deck['turns'] = []

    order_ct = 0

    for idx, turn in enumerate(turns):
        owner = name_to_owner[turn['name']]
        owner['turns'].append(turn)
        if not 'order' in owner:
            owner['order'] = idx + 1
            order_ct += 1
        del turn['name']

    if order_ct != len(game_dict['decks']):
        raise BogusGame('Did not find turns for all players')

def validate_names(decks):
    """ Raise an exception for names that might screw up the parsing.  
    This should happen in 1% of real games, but it's just easier to punt
    on annoying inputs that to make sure we get them right."""
    used_names = set()
    for deck in decks:
        name = deck['name']
        if name in used_names:
            raise BogusGame('Duplicate name %s' % name)
        used_names.add(name)

        if name[0] == '.':
            raise BogusGame('name %s starts with period' % name)
        for kword in KEYWORDS:
            if kword.lstrip() in name or kword.rstrip() in name:
                raise BogusGame('name %s contains keyword %s' % (name, kword))

    if len(used_names) != len(decks):
        raise BogusGame('not everyone took a turn?')
    if len(decks) <= 1:
        raise BogusGame('only one player')

def _player_label(idx):
    """ Return label for player index """ 
    return 'player' + str(idx + 1)

def parse_game(game_str, dubious_check = False):
    """ Parse game_str into game dictionary

    game_str: Entire contents of an isotropic log file.
    dubious_check: If true, raise a BogusGame exception if the game is
      suspicious.

    returns a dict with the following fields:
      decks: A list of player decks, as documend in parse_deck().
      supply: A list of cards in the supply.
      players: A list of normalized player names.
      game_end: List of cards exhausted that caused the game to end.
      resigned: True iff some player in the game resigned..
    """
    try:
        split_sects = SECTION_SEP.split(game_str)
        header_str, decks_blob, trash_and_turns = split_sects
    except ValueError, exception:
        print len(split_sects), SECTION_SEP.split(game_str), game_str
        raise exception
    game_dict = parse_header(header_str)
    decks = parse_decks(decks_blob)
    game_dict['decks'] = decks
    validate_names(decks)

    turns_str = trash_and_turns.split('Game log')[1]
    turns_str = turns_str[turns_str.find('---'):]
    
    turns = parse_turns(turns_str)
    
    associate_game_with_norm_names(game_dict)
    associate_turns_with_owner(game_dict, turns)
    assign_win_points(game_dict)

    if dubious_check and Game(game_dict).DubiousQuality():
        raise BogusGame('Dubious Quality')

    return game_dict

def parse_header(header_str):
    """ Parse the header string.

    Return a dictionary with game_end, supply, and resigned fields, 
      like parse_game.
    """
    sections = [s for s in header_str.replace(' \n', '\n').split('\n\n') if s]
    end_str, supply_str = sections
    assert 'gone' in end_str or 'resigned' in end_str
    if 'gone' in end_str:
        resigned = False
        gone = capture_cards(end_str.split('\n')[1])
    else:
        resigned = True
        gone = []
    supply = capture_cards(supply_str)
    return {'game_end': gone, 'supply': supply, 
            'resigned': resigned}

PLACEMENT_RE = re.compile('#\d (.*)')
POINTS_RE = re.compile(': (-*\d+) points(\s|(\<\\/b\>))')

def parse_deck(deck_str):
    """ Given an isotropic deck string, return a dictionary containing the
    player names
    
    deck_str: starts with placement and name, ends with last card in deck.
    returns dictionary containing the following fields
      name: 
      vp_tokens: number of vp tokens.
      deck: Dictionary of name, frequency packages.
      resigned: True iff this player resigned
    """
    name_vp_list, _opening, deck_contents = deck_str.split('\n')
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
    name, _points_or_resign = (name_points[:last_colon_in_name_points],
                               name_points[last_colon_in_name_points + 1:])

    def cleanup_name(name):
        """ Given a name and placement, get rid of the bold tags and  """
        htmlless_name = name.replace('<b>', '').replace('</b>', '')
        placement_match = PLACEMENT_RE.match(htmlless_name)
        if placement_match:
            return placement_match.group(1)
        return htmlless_name

    name = cleanup_name(name)

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
            except KeyError, exception:
                print chunk, card_name, card_blob[right_bracket_index - 10:]
                raise exception
            card_quant = int(card_blob.split()[0])
            deck_comp[card_name] = card_quant
    return {'name': name, 'points': points, 'resigned': resigned,
            'deck': deck_comp, 'vp_tokens': vp_tokens}

def parse_decks(decks_blob):
    """ Parse and return a list of decks"""
    deck_blobs = [s for s in decks_blob.split('\n\n') if s]
    return [parse_deck(deck_blob) for deck_blob in deck_blobs]

def name_and_rest(line, term):
    """ Split line about term, return (before, after including term). """
    start_of_term = line.find(term)
    assert start_of_term != -1

    def _strip_leading(val, dead_chars):
        for idx, char in enumerate(val):
            if char not in dead_chars:
                return val[idx:]
        return ''

    name = _strip_leading(line[:start_of_term], ' .').strip()
    return name, line[start_of_term + len(term):]

def _delete_keys_with_empty_vals(dict_obj):
    """ Remove keys from object that are associated with False objects."""
    keys_to_die = []
    for k in dict_obj:
        if not dict_obj[k]:
            keys_to_die.append(k)
    for k in keys_to_die:
        del dict_obj[k]

def count_money(plays):
    """ Return the value of the money from playing cards in plays.

    This does not include money from cards like Steward or Bank, but does
    count Copper. 

    plays: list of cards.
    """
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

def parse_turn(turn_blob):
    """ Parse the information from a given turn.

    Return a dict containing the following fields.  If any of the fields have
    a value that evaluates to False, do not keep it.
    
    name: player name.
    number: 1 indexed turn number.
    plays: List of cards played.
    buys: List of cards bought.
    gains: List of cards gained.
    trashes: List of cards trashed.
    returns: List of cards returned.
    money: Amount of money available during entire buy phase.
    opp: Dict keyed by opponent name, containing dicts with trashes/gains.
    """
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
                trashes.extend(capture_cards(line[:gain_start]))
                gains.extend(capture_cards(line[gain_start:]))
                continue            
            if line.endswith(KW_TRASHES_IT):
                if KW_TURNS_UP_A in line:
                    # Swinder turn
                    last_noted_player, rest = name_and_rest(line, 
                                                            KW_TURNS_UP_A) 
                elif KW_REVEALS_A in line:
                    # Sab turn
                    last_noted_player, rest = name_and_rest(line, KW_REVEALS_A)
                else:
                    assert False, 'Did not handle trashing in line %s' % line 
                
                opp_turn_info[last_noted_player]['trashes'].extend(
                    capture_cards(line))

            opp_n, rest = name_and_rest(line, KW_TRASHES)
            if opp_n == name:
                trashes.extend(capture_cards(rest))
            else:
                cards_opp_trashed = capture_cards(rest)
                if cards_opp_trashed:
                    opp_turn_info[opp_n]['trashes'].extend(cards_opp_trashed)

        if KW_WITH_A in line:
            if KW_REPLACING in line:
                assert last_noted_player in line
                new_gained_portion = line[line.find(KW_WITH_A):]
                opp_turn_info[last_noted_player]['gains'].extend(capture_cards(
                        new_gained_portion))
        if KW_PLAYS in line: 
            plays.extend(capture_cards(line))
        if has_gaining and not KW_TOKEN in line: 
            gains.extend(capture_cards(line[line.find(KW_GAINING):])) 
        if KW_BUYS in line: 
            buys.extend(capture_cards(line))
        if has_trashing: 
            trashes.extend(capture_cards(line))
        if KW_GAINS_A in line and not KW_TOKEN in line:
            opp_name, rest = name_and_rest(line, KW_GAINS_A)
            if KW_DISCARDS in opp_name:  
                opp_name = opp_name[:opp_name.find(KW_DISCARDS)]
            opp_turn_info[opp_name]['gains'].extend(capture_cards(rest))
        if KW_IS_TRASHED in line:
            # Saboteur after revealing cards, name not mentioned on this line.
            assert last_noted_player != None, line
            cards = capture_cards(line)
            opp_turn_info[last_noted_player]['trashes'].extend(cards)
        if KW_REVEALS in line:
            last_noted_player, rest = name_and_rest(line, KW_REVEALS)
            card_revealed = capture_cards(line)

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
            returns.extend(capture_cards(line))
        if KW_GETTING in line or KW_GETS in line:
            money_match = GETTING_MONEY_RE.search(line)
            if money_match:
                turn_money += int(money_match.group(1))
        if KW_WHICH_IS_WORTH in line:
            worth_match = WHICH_IS_WORTH_RE.search(line)
            assert bool(worth_match), line
            turn_money += int(worth_match.group(1))
            
    for opp in opp_turn_info:
        _delete_keys_with_empty_vals(opp_turn_info[opp])
    # TODO:  Consider getting rid of turn number from the DB?  It's easy
    # to recompute from the game state anyway, and it would save some space.
    ret = {'name': name, 'number': turn_no, 'plays': plays , 
           'buys': buys, 'gains': gains, 'trashes': trashes, 
           'returns': returns, 'money': count_money(plays) + turn_money,
           'opp': dict(opp_turn_info)}

    _delete_keys_with_empty_vals(ret)
    return ret

def parse_turns(turns_blob):
    """ Return a list of turn objects, as documented by parse_turn(). """
    turns = []
    turn_blobs = TURN_HEADER_NO_GROUP_RE.split(turns_blob)
    if turn_blobs[0].strip() == '':
        turn_blobs = turn_blobs[1:]
    turn_headers = TURN_HEADER_NO_GROUP_RE.findall(turns_blob)
    for turn_header, turn_blob in zip(turn_headers, turn_blobs):
        turns.append(parse_turn(turn_header + turn_blob))
    return turns

def outer_parse_game(filename):
    """ Parse game from filename. """
    contents = codecs.open(filename, 'r', encoding='utf-8').read()
    if not contents:
        print 'empty game'
        return None
    if '<b>game aborted' in contents:
        print 'skipping aborted game', filename
        return None
    try:
        parsed = parse_game(contents, dubious_check = True)
        parsed['_id'] = filename.split('/')[-1]
        return parsed
    except BogusGame, bogus_game_exception:
        print 'skipped', filename, 'because', bogus_game_exception.reason
        return None

# http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
def segments(lis, chunk_size):
    """ Return an iterator over sublists whose size matches chunk_size. """
    for i in xrange(0, len(lis), chunk_size):
        yield lis[i:i + chunk_size]

def dump_segment(arg_tuple):
    """ Write a json serialized version of games to to name determined by 
    arg tuple.
    """
    idx, year_month_day, segment = arg_tuple
    out_name = 'parsed_out/%s-%d.json' % (year_month_day, idx)
    json.dump(segment, open(out_name, 'w'), indent=2, sort_keys=True)

def convert_to_json(year_month_day, games_to_parse = None):
    """ Parse the games in for given year_month_day and output them
    into split local files.

    year_month_day: string in yyyymmdd format encoding date
    games_to_parse: if given, use these games rather than all files in dir.
    """
    if games_to_parse is None:
        games_to_parse = os.listdir('static/scrape_data/' + year_month_day)
        games_to_parse = ['static/scrape_data/' + year_month_day + '/' + g 
                          for g in games_to_parse if g.endswith('html')]

    if not games_to_parse:
        print 'no data files to parse in ', year_month_day
        return

    # games_to_parse = games_to_parse[:100]
    pool = multiprocessing.Pool()
    parsed_games = pool.map(outer_parse_game, games_to_parse, 
                            chunksize=50)
    #parsed_games = map(outer_parse_game, games_to_parse)
    print year_month_day, 'before filtering', len(parsed_games)
    parsed_games = [x for x in parsed_games if x]

    # wrongness = collections.defaultdict(int)
    # overall = collections.defaultdict(int)
    # for raw_game in parsed_games:
    #     accurately_parsed = check_game_sanity(game.Game(raw_game))
    #     if not accurately_parsed:
    #         print raw_game['_id']
    #     for card in raw_game['supply']:
    #         if not accurately_parsed:
    #             wrongness[card] += 1
    #         overall[card] += 1

    # ratios = []
    # for card in overall:
    #     ratios.append(((float(wrongness[card]) / overall[card]), card))
    # ratios.sort()
    # print ratios[-10:]

    print year_month_day, 'after filtering', len(parsed_games)
    game_segments = list(segments(parsed_games, 100))
    labelled_segments = [(i, year_month_day, c) for i, c in
                         enumerate(game_segments)]
    pool.map(dump_segment, labelled_segments)

def parse_game_from_file(filename):
    """ Return a parsed version of a given filename. """
    contents = codecs.open(filename, 'r', encoding='utf-8').read()
    return parse_game(contents, dubious_check = True)

def check_game_sanity(game_val):
    """ Check if if game_val is self consistent. 

    In particular, check that the the player decks match the result of 
    simulating the saved games through the deck."""
    
    last_state = None
    game_state_iterator = game_val.GameStateIterator()
    for game_state in game_state_iterator:
        last_state = game_state
    for player_deck in game_val.PlayerDecks():
        parsed_deck_comp = player_deck.Deck()
        computed_deck_comp = last_state.GetDeckComposition(
            player_deck.Name()) 

        _delete_keys_with_empty_vals(parsed_deck_comp)
        computed_dict_comp = dict(computed_deck_comp)
        _delete_keys_with_empty_vals(computed_dict_comp)
        
        if parsed_deck_comp != computed_deck_comp:
            found_something_wrong = False
            for card in set(parsed_deck_comp.keys() + 
                            computed_deck_comp.keys()):
                if parsed_deck_comp.get(card, 0) != computed_deck_comp.get(
                    card, 0):

                    print card, parsed_deck_comp.get(card, 0), \
                        computed_deck_comp.get(card, 0)
                    found_something_wrong = True
            if found_something_wrong:
                print player_deck.Name(), game_val.Id()
                print
                return False
    return True

def main():
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

        convert_to_json(year_month_day)

def annotate_game(contents):
    """ Decorate game contents with some JS that makes a score keeper 
    and provides anchors per turn."""
    parsed_game = parse_game(contents, dubious_check = False)
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
    
# def profilemain():
#     import hotshot, hotshot.stats
#     prof = hotshot.Profile("parse_game.prof")
#     prof.runcall(t)
#     prof.close()
#     stats = hotshot.stats.load("parse_game.prof")
#     stats.strip_dirs()
#     stats.sort_stats('time', 'calls')
#     stats.print_stats(20)

if __name__ == '__main__':
    utils.ensure_exists('parsed_out')
    main()
    
