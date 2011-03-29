function RenderPage() {
    

    var card_data = {
	    'chapel': [1.2, 1.5],
	    'peddler': [1.3, 1.2],
    };
    // $('#buy_data').setTemplateElement('buy_data_template');
    //$('#buy_data').processTemplate(card_data);
    var temp = $.getTemplate('#buy_data_template');
    console.log(temp);
    var t = $.processTemplateToText(temp, card_data);
    console.log(t);
};

//    $.getJSON('/popular_buys?player=rrenaud&type=json', function(data) {
// 
//	      }
//	     );

$(document).ready(RenderPage);
