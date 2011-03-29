function RenderPage() {
    var card_data = {
	cards: [
	    {cardname: 'chapel', w:1.2},
	    {cardname: 'peddler', w:1.5}
	    ]
    };
    var rendered = ich.buy_data_template(card_data, true);
    console.log(rendered);
    $('#buy_data').html(rendered);
};

//    $.getJSON('/popular_buys?player=rrenaud&type=json', function(data) {
// 
//	      }
//	     );

$(document).ready(RenderPage);
