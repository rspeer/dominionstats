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

function DecorateGame() {
  game.decks.sort(function(a, b) { return a.order - b.order; });

  for (var i = 0; i < card_list.length; ++i) {
    keyed_card_info[card_list[i].Singular] = card_list[i];
  }

  $('#game-display').css({position: 'fixed', background: '#ffffff',
			  bottom: 0, 'border-style': 'groove', padding:'3px'
			 });

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
  console.log("RenderGameState " + state_ind);
  var state = game.game_states[state_ind];
  var rendered = RenderCardFreqs(state.supply);

  rendered += game.game_states[state_ind].display_label + '<br>\n';

  for (var i = 0; i < game.decks.length; ++i) {
    var name = game.decks[i].name;
    rendered += name + ': ' +
      RenderCardFreqLine(state.player_decks[name]) + '<br>';
  }
  return rendered;
}

function UpdateDisplay() {
  console.log("UpdateDisplay");
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
