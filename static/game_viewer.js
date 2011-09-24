var keyed_card_info = {};

// This snippet is from
// http://stackoverflow.com/questions/769701/is-there-a-way-to-detect-when-an-html-element-is-hidden-from-view
function IsScrolledIntoView(elem, bottom_buffer) {
  var docViewTop = $(window).scrollTop();
  var docViewBottom = docViewTop + $(window).height();
  var elemTop = $(elem).offset().top;
  var elemBottom = elemTop + $(elem).height();
  if (bottom_buffer) docViewBottom -= bottom_buffer;
  return ((elemBottom >= docViewTop) && (elemTop <= docViewBottom));
}

function ScoreExtractor(player, game_state) {
  return game_state.scores[player];
}

var NOT_VALID_VALUE_SENTINEL = -101;

function MoneyExtractor(player, game_state) {
  if (game_state.player == player) {
    return game_state.money;
  }
  return NOT_VALID_VALUE_SENTINEL;
}

function WinProbExtractor(player, game_state) {
  if (game_state.player == player) {
    return game_state.win_prob;
  }
  return NOT_VALID_VALUE_SENTINEL;
}

function MakeSeriesForPlayer(player_name, extractor) {
  var data_list = [];
  var output_per_turn_ct = [];  // make it so p1 and p2 turn x don't overdraw.
  var num_players = game.players.length;
  for (var i = 0; i < game.game_states.length; ++i) {
    // We could do something fancy/complicated with poss/outpost turns,
    // but it's probably not worth it.
    var game_state = game.game_states[i];
    var turn = game_state.turn_no;
    var extracted = extractor(player_name, game_state);
    if (extracted != NOT_VALID_VALUE_SENTINEL) {
      if (turn >= output_per_turn_ct.length) output_per_turn_ct[turn] = 0;
      var offset = Math.min(output_per_turn_ct[turn], num_players - 1) /
                     num_players;
      data_list.push([turn + offset, extracted]);
      output_per_turn_ct[turn]++;
    }
  }
  return {
    label: player_name, data: data_list
  };
}

function MakeSeriesForPlayers(extractor) {
  var point_lists = [];
  for (var i = 0; i < game.players.length; ++i) {
    point_lists.push(MakeSeriesForPlayer(game.players[i], extractor));
  }
  return point_lists;
}

function DecorateGame() {
  game.decks.sort(function(a, b) { return a.order - b.order; });

  for (var i = 0; i < card_list.length; ++i) {
    keyed_card_info[card_list[i].Singular] = card_list[i];
  }

  $('#game-display').css({position: 'fixed', background: '#ffffff',
			  bottom: 0, 'border-style': 'groove', padding:'3px'
			 });

  var game_states = game.game_states;
  var last_state = game_states[game_states.length - 2];

  var xaxis_max = last_state.turn_no + 1;

  function format(number) {
    var asStr = '<div style="width:30px">' + number + '</div>';
    return asStr;
  }

  // Try to make sure the graphs are vertically aligned by making sure they
  // have the same axis extents even though the score has an additional
  // turn over money because of the end game, and by making sure the x axis
  // labels use the same number of characters, even though the scores tend
  // to be longer and possibly negative.
  var graph_opts = {
    legend: { position: 'nw'},
    xaxis: { tickDecimals: 0,  max: xaxis_max},
    yaxis: { tickDecimals: 0, tickFormatter: format}
  };

  $.plot($('#score-graph'), MakeSeriesForPlayers(ScoreExtractor), graph_opts);
  $.plot($('#money-graph'), MakeSeriesForPlayers(MoneyExtractor), graph_opts);

  graph_opts.yaxis.position = { max: 1.0 };

  $.plot($('#win-prob-graph'),
     MakeSeriesForPlayers(WinProbExtractor), graph_opts);

  $(window).scroll(UpdateDisplay);
}

function RenderCardFreqLine(freqs, cards) {
  if (cards == null) {
    cards = [];
    for (card in freqs) cards.push(card);
    SortCardsByCost(cards);
  }
  var ret = '';
  var first = true;
  for (var i = 0; i < cards.length; ++i) {
    if (!first) ret += ', ';
    first = false;
    ret += freqs[cards[i]] + ' ' + cards[i];
  }
  return ret;
}

function SortCardsByCost(cards) {
  function Cost(card) {
    var cost = keyed_card_info[card]['Cost'];
    if (cost[0] == 'P') {  // Pretend potions are worth 2.5 coins
      cost = parseInt(cost[1]) + 2.5;
    }
    return parseInt(cost);
  }

  function LexicographicCostThenName(a, b) {
    var cost_diff = Cost(b) - Cost(a);
    if (cost_diff != 0) return cost_diff;
    if (a < b) return -1;
    if (a == b) return 0;
    return 1;
  }

  cards.sort(LexicographicCostThenName);
}

function RenderCardFreqs(card_freqs) {
  var cards_by_cost = [];

  for (card in card_freqs) {
    cards_by_cost.push(card);
  }
  SortCardsByCost(cards_by_cost);

  var vp = [], actions = [], coins = [];
  for (var i = 0; i < cards_by_cost.length; ++i) {
    var card = cards_by_cost[i];
    var card_inf = keyed_card_info[card];
    if (card_inf['Victory'] == '1' || card == 'Curse') vp.push(card);
    else if (card_inf['Action'] == '1') actions.push(card);
    else coins.push(card);
  }

  return RenderCardFreqLine(card_freqs, vp) + '<br>\n' +
    RenderCardFreqLine(card_freqs, actions) + '<br>\n' +
    RenderCardFreqLine(card_freqs, coins) + '<br>\n';
}

function RenderGameState(state_ind) {
  var state = game.game_states[state_ind];
  var rendered = RenderCardFreqs(state.supply);

  rendered += state.display_label + '<br>\n';

  for (var i = 0; i < game.decks.length; ++i) {
    var name = game.decks[i].name;
    rendered += name + ': ' + state.scores[name] + ' points : ' +
      RenderCardFreqLine(state.player_decks[name]) + '<br>';
  }
  return rendered;
}

function UpdateDisplay() {
  var max_active = -1;
  var game_display_height = $('#game-display').height();
  for (var i = 0; i < game.game_states.length; ++i) {
    var elem = $('#' + game.game_states[i].label);
    if (elem && IsScrolledIntoView(elem, game_display_height)) {
      max_active = i;
    }
  }
  if (max_active >= 0) {
    $('#game-display').html(RenderGameState(max_active));
  }
}
