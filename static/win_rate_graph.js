function MeanVarStat(mvs_data) {
  mvs_data.freq = mvs_data.freq || mvs_data[0];
  mvs_data.sum = mvs_data.sum || mvs_data[1];
  mvs_data.sum_sq = mvs_data.sum_sq || mvs_data[2];
  var mvs = {};
  mvs.Mean =  function() { return (mvs_data.sum + 2) / (mvs_data.freq + 2); };
  mvs.Variance = function() {
    if (mvs_data.freq <= 1) {
      return 1e10;
    }
    return ((mvs_data.sum_sq + 4) - ((mvs_data.sum+2) * (mvs_data.sum+2)) /
	    (mvs_data.freq + 1)) / (mvs_data.freq + 1);
  };
  mvs.SampleStdDev = function() {
    return Math.sqrt(mvs.Variance() / (mvs_data.freq + 2));
  };
  mvs.Freq = function() {
    return mvs_data.freq;
  };
  return mvs;
};

var card_list;

function GetCardInfo() {
  var c = $.ajax(
    {url: 'static/card_list.js',
     dataType: 'json',
     success: function(data) {
       // hack, I don't understand this, according to the
       // docs, this should be parsed for me already.
       card_list = eval(data);
       RefreshCardGraph(graph_type);
     }});
};

function ExpandCardGlob(glob) {
  var ret = [];
  try {
    // This should probably be an object to avoid the linear search.
    for (var i = 0; i < card_list.length; ++i) {
      var per_card_attrs = card_list[i];
      if (glob.toLowerCase() == per_card_attrs.Singular.toLowerCase()) {
	ret.push(per_card_attrs.Singular);
	return ret;
      }
    }

    for (var i = 0; i < card_list.length; ++i) {
      var per_card_attrs = card_list[i];
      for (k in per_card_attrs) {
	var val = per_card_attrs[k];
	if (isNaN(parseInt(val))) {
	  eval(k + '= "' + val + '"');
	} else {
	  eval(k + '=' + val);
	}
      }
      if (eval(glob)) {
	ret.push(per_card_attrs.Singular);
      }
    }
  } catch (err) {
    console.log(err);
  }
  return ret;
};

function WeightAllTurnsSame(x_val) {
  return 1;
}

function WeightProportionalToAccumDiff(x_val) {
  return x_val;
};

function DisplayCardData(card_names_str, graph_name, weight_func) {
  function GrabDataIntoSeries(card) {
    var card_stat = all_card_data.card_stats[card];
    var total_games_available = card_stat.available;
    var point_data = card_stat[graph_name];
    var series = [];
    keys = [];
    for (var diff in point_data) {
      keys.push(diff);
    }
    keys.sort(function(a, b) { return a - b; });
    var quality = 0;
    for (var i = 0; i < keys.length; ++i) {
      var mean_var_stat = MeanVarStat(point_data[keys[i]]);
      var std_dev = mean_var_stat.SampleStdDev() * 2;
      if (mean_var_stat.Freq() > 50 && std_dev < .1) {
	series.push([keys[i],
		     mean_var_stat.Mean(),
		     std_dev
		    ]);
      }
      var prob = mean_var_stat.Freq() / total_games_available;
      // consider subtracting out a standard dev or two to prevent
      // over-fitting.
      var goodness = mean_var_stat.Mean() - 1.0;
      var weight = weight_func(keys[i]);
      quality += prob * goodness * weight;
    }

    var point_opts = {
      errorbars: "y",
      yerr: {
	show: true, upperCap: '-', lowerCap: '-'
      }
    };

    return {label: card, points: point_opts, data: series, quality: quality};
  };

  function MinOfSeries(series) {
    var mn = 500;
    for (var i = 0; i < series.length; ++i) {
      mn = Math.min(mn, series[i][1] - series[i][2]);
    }
    return mn;
  };

  function MaxOfSeries(series) {
    var mx = -1;
    for (var i = 0; i < series.length; ++i) {
      mx = Math.max(mx, series[i][1] + series[i][2]);
    }
    return mx;
  };

  var card_exprs = card_names_str.split(',');
  var series_list = [];
  for (var i = 0; i < card_exprs.length; ++i) {
    var card_name_or_glob = card_exprs[i].trim();
    var card_names = ExpandCardGlob(card_name_or_glob);
    for (var j = 0; j < card_names.length; ++j) {
      if (all_card_data.card_stats[card_names[j]]) {
	series_list.push(GrabDataIntoSeries(card_names[j]));
      } else {
	console.log('bogus ' + card_name);
	// handle bogus card name?
      }
    }
  }

  series_list.sort(function(a, b) {
		     return b.quality - a.quality;
		   });

  var mn = 5000;
  var mx = -1;
  for (var i = 0; i < series_list.length; ++i) {
    mn = Math.min(MinOfSeries(series_list[i].data), mn);
    mx = Math.max(MaxOfSeries(series_list[i].data), mx);
  }

  var range = mx - mn;
  var fraction_buffer = .05;

  $.plot($("#placeholder"),
	 series_list,
	 {   xaxis: { },
	     yaxis: {  min: mn - range * fraction_buffer,
		       max: mx + range * fraction_buffer
		    },
	     legend: { position: 'nw' } 
	     
	 }
  );
};

function RefreshCardGraph(graph_type) {
  DisplayCardData($('#card_names').val(), graph_type, weight_func);
  var wl = window.location;
  var new_url = ('http://' + wl.host + wl.pathname + '?cards=' +
		 encodeURIComponent($('#card_names').val()));

  if (typeof(window.history.pushState) == 'function') {
    window.history.pushState(null, new_url, new_url);
  }

  $('#collection_info').html
  ('Total of ' + all_card_data.num_games + ' games analyzed<br>' +
   'The most recent game was on ' +
   all_card_data.max_game_id.substr(5, 8) + '<br>');
};

function DisplayUrl() {
  var wl = window.location;
  var new_url = ('http://' + wl.host + wl.pathname + '?cards=' +
		 encodeURIComponent($('#card_names').val()));
  $('#url_display').val(new_url);
  var offset = $('#getlink').offset();
  $('#url_display').css(
    { left:offset.left, top:offset.top,
      height:"25px"}
  ).show().select();
};

$(document).click(
  function (e) {
    if (e.target.id != "getlink") {
      $('#url_display').hide();
    }
  }
);

function MakeTable() {
  var table_contents = '<table>';
  for (var card in all_card_data.card_stats) {
    var per_card_data = all_card_data.card_stats[card];
    var any_accum_data = per_card_data.win_any_accum;
    var mvs_any_accum = MeanVarStat(any_accum_data);
    var prob_any_gained = mvs_any_accum.Freq() / per_card_data.available;

    table_contents += ('<tr>' +
		       '<td>' + card + '</td>' +
		       '<td>' + prob_any_gained + '</td>' +
		       '<td>' + mvs_any_accum.Mean() + '</td>' +
		       '</tr>');
  }
  table_contents += '</table>';
  // $('#card_data_table').html(table_contents);
}

jQuery.event.add(window, "load", GetCardInfo);
// jQuery.event.add(window, "load", MakeTable);
