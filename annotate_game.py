""" Nicely render a game with deck composition viewer and some graphs of
the game as it progresses."""

import itertools
import simplejson as json

import game
import parse_game
# import rf_predict

def _pretty_format_html(v):
    return '<br>' + pprint.pformat(v).replace(
        '\n', '<br>').replace(' ', '&nbsp')

# win_predictor = rf_predict.WinPredictor()

def annotate_game(contents, game_id, debug=False):
    """ Decorate game contents with some JS that makes a score keeper 
    and provides anchors per turn."""
    contents = contents.replace('&mdash;', '---')
    parsed_game = parse_game.parse_game(contents, dubious_check = False)
    states = []
    
    game_val = game.Game(parsed_game)
    # predictions = win_predictor.predict_all_turns(game_val)
    for game_state in itertools.izip(
        game_val.game_state_iterator(), #predictions
        ):
        encoded = game_state.encode_game_state()
        #encoded['win_prob'] = win_prob
        states.append(encoded)

    parsed_game['game_states'] = states

    ret = u''

    start_body = contents.find('<body>') + len('<body>')
    ret += contents[:start_body]
    ret += """
<div id="game-display"></div>
<script src="static/flot/jquery.js"></script>
<script src="static/game_viewer.js"></script>
<script src="static/flot/jquery.js"></script>
<script src="static/flot/jquery.flot.js"></script>
<script type="text/javascript">
        var game = %s;
        var card_list = %s;
        $(document).ready(DecorateGame);
</script>
""" % (json.dumps(parsed_game, indent=2), 
       open('static/card_list.js', 'r').read())
    contents = contents[start_body:]
    if debug > 2:
        ret += _pretty_format_html(parsed_game)
    if debug > 1:
        for turn in game_val.get_turns():
            ret += '%d %d %d %s %s<br>' % (
                turn.get_turn_no(),
                turn.get_player().TurnOrder(), turn.get_poss_no(),
                turn.turn_dict.get('poss', False),
                turn.get_player().name())

    import cStringIO as StringIO
    output_buf = StringIO.StringIO()
    if not parse_game.check_game_sanity(game_val, output_buf):
        ret += 'Parsing error, data mismatch, '
        ret += '''<a href="game?game_id=%s&debug=1">be a hero, find the 
bug</a> and tell rrenaud@gmail.com<br>''' % game_id
        ret += output_buf.getvalue().replace('\n', '<br>\n')

    cur_turn_ind = 0
    
    split_turn_chunks = parse_game.split_turns(contents)
    ret += split_turn_chunks[0]
    split_turn_chunks.pop(0)

    for idx, (turn_chunk, game_state) in enumerate(
        itertools.izip(split_turn_chunks, game_val.game_state_iterator())):
        split_chunk = turn_chunk.split('\n')

        turn_id = game_state.turn_label()
        show_turn_id = game_state.turn_label(for_anchor=True)
        ret += '<div id="%s"></div>' % turn_id
        ret += '<a name="%s"></a><a href="#%s">%s</a>' % (
            show_turn_id, show_turn_id, split_chunk[0])

        if debug:
            ret += '<br>' + repr(game_val.get_turns()[cur_turn_ind]).replace(
                '\n', '<br>')
        cur_turn_ind += 1

        if idx != len(split_turn_chunks) - 1:
            ret += turn_chunk[turn_chunk.find('\n'):]
        else:            
            before_end = turn_chunk.find('</html')
            ret += turn_chunk[turn_chunk.find('\n'): before_end]
            ret += """
<div id="end-game"></div>
<table>
  <tr>
    <td width=50px>score</td>
    <td><div id="score-graph" style="width:1000px;height:250px;"></div></td>
  </tr>
  <tr>
    <td width=50px>money</td>
    <td><div id="money-graph" style="width:1000px;height:250px;"></div></td>
  </tr>
  <tr>
    <td width=50px>win prob</td>
    <td><div id="win-prob-graph" style="width:1000px;height:250px;"></div></td>
  </tr>
</table>
"""
            ret += '</div>&nbsp<br>\n' * 10 
            ret += '</html>'
    return ret
