import axios from 'axios';
import $ from 'jquery';

console.log('content_scripts for Dozen Reinvent Enhance Website')

var numberOfRequestsSent = 0
var maxRequestsSent = 50
if (window.location.href === 'https://www.portal.reinvent.awsevents.com/connect/mySchedule.ww') {
	window.sessions = [];
	var send = {
		method: 'POST',
		url: 'https://vyr5ooq5hzcyrlapt47x4mwk4m.appsync-api.us-east-1.amazonaws.com/graphql',
		data: {"query": "query {getPaginatedSessions {sessions {id\n abbr\n room}, nextToken}}" },
		headers: {
			'x-api-key': 'da2-5vvhlmv4cbfvbb7eiofilktd6u'
		},
		json: true
	};
	axios(send)
		.then((res) => {
			console.log(res);
			window.sessions = res.data.data.getPaginatedSessions.sessions;
			getNextSessions(res.data.data.getPaginatedSessions.nextToken);
		})
}

function getNextSessions(nextToken) {
	var send = {
		method: 'POST',
		url: 'https://vyr5ooq5hzcyrlapt47x4mwk4m.appsync-api.us-east-1.amazonaws.com/graphql',
		data: {"query": "query {getPaginatedSessions(nextToken: \"" + nextToken + "\") {sessions {id\n room\n abbr}, nextToken}}" },
		headers: {
			'x-api-key': 'da2-5vvhlmv4cbfvbb7eiofilktd6u'
		},
		json: true
	};
	axios(send)
		.then((res) => {
			console.log(res);
			if (res.data.data.getPaginatedSessions) {
				for (var i = res.data.data.getPaginatedSessions.sessions.length - 1; i >= 0; i--) {
					window.sessions.push(res.data.data.getPaginatedSessions.sessions[i]);
				}
				nextToken = res.data.data.getPaginatedSessions.nextToken;
				if (numberOfRequestsSent++ < maxRequestsSent) {
					getNextSessions(nextToken);
				} else {
					populateLocationDivs();
				}
			} else {
				// setInterval(() => {
					populateLocationDivs();
				// }, 3000);
			}
		})
}

function populateLocationDivs() {
	console.log($(".fc-event"));
	var table = $(".fc-agenda > div > div > div");
	for (var i = $(".fc-event").length - 1; i >= 0; i--) {
		var title = $($(".fc-event")[i].getElementsByClassName("fc-event-title")[0])[0].innerHTML
		var abbr = title.substring(0, title.indexOf(" "));
		var session = window.sessions.find((s) => s.abbr === abbr + " -"); //.substring(0, s.abbr.length)
		if (session && session.room) {
			var hotel = session.room.substring(0, session.room.indexOf(","));
			if (hotel === "Aria East" || hotel === "Aria West") {
				hotel = "Aria";
			}
			var div = $("<div class='drew-location drew-" + hotel + "'>" + hotel + "</div>");
			var fcEvent = $($(".fc-event")[i]);
			div.attr('style', 'top: ' + (fcEvent.position().top + fcEvent.height() - 40) + 'px;left:' + fcEvent.position().left + 'px;width: ' + fcEvent.width() + 'px;')
				.attr('id', 'drew-location-' + i);
			table.append(div);
		} 
	}
}


$("#mySchedule").attr('style','width: 1900px')
$(".fc-sun,.fc-mon,.fc-tue,.fc-wed,.fc-thu,.fc-fri").attr('style', '')
var resizeEvent = window.document.createEvent('UIEvents'); 
resizeEvent .initUIEvent('resize', true, false, window, 0); 
window.dispatchEvent(resizeEvent);
var div = $("<div />", {
	html: '&shy;<style>.drew-location { position: absolute;bottom: 0px;font-size: 40px;text-align: center; z-index:9; height: 40px} .drew-Mirage { background-color: black; color: white } .drew-Aria { background-color: blue; color: white } .drew-Venetian { background-color: red; color: white } .drew-Bellagio { background-color: purple; color: white } .drew-MGM { background-color: green; color: black }</style>'
}).appendTo("body");    


// curl -XPOST -H "Content-Type:application/graphql" -H "x-api-key:da2-5vvhlmv4cbfvbb7eiofilktd6u" -d '{"query": "query {getPaginatedSessions {sessions {id\n room}, nextToken}}" }' https://vyr5ooq5hzcyrlapt47x4mwk4m.appsync-api.us-east-1.amazonaws.com/graphql