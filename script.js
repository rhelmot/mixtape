var root_url;
var dir_url;
var playlist_name;
var current_track;
var playlist_data;

function parse_fragments() {
	var pieces = location.href.split('#', 2);
	root_url = pieces[0];
	if (root_url.endsWith('/')) {
		dir_url = root_url.slice(0, -1);
	} else if (root_url.endsWith('/index.html')) {
		dir_url = root_url.slice(0, -11);
	} else {
		dir_url = root_url;
	}

	var fragment_str = pieces[1];
	if (fragment_str) {
		var fragment_list = fragment_str.split('&');
		var fragment = {};
		for (var i = 0; i < fragment_list.length; i++) {
			var fragment_piece = fragment_list[i].split('=', 2);
			fragment[fragment_piece[0]] = fragment_piece[1];
		}
		return fragment;
	} else {
		return {};
	}
}

function set_url() {
	location.href = root_url + '#playlist=' + playlist_name + '&track=' + current_track.toString();
}

function play_track(n) {
	current_track = n;
	set_url();
	var track = playlist_data.tracks[n];
	$('#tracktitle').text(track.title || track.name);
	$('#trackartist').text(track.artist);
	$('#trackalbum').text(track.album || 'Unknown album');
	var paragraphs = track.description.split('\n\n');
	var descr = $('#description')[0];
	descr.innerHTML = '<p><em>' + (n+1).toString() + '/' + playlist_data.tracks.length.toString() + '</em></p>';
	for (var i = 0; i < paragraphs.length; i++) {
		var p = document.createElement('p');
		p.innerText = paragraphs[i];
		descr.appendChild(p);
	}

	if (n == 0) {
		$('#arrow-left').removeClass('active');
	} else {
		$('#arrow-left').addClass('active');
	}

	if (n == playlist_data.tracks.length - 1) {
		$('#arrow-right').removeClass('active');
	} else {
		$('#arrow-right').addClass('active');
	}

	var audio = $('#goodstuff')[0];
	audio.currentTime = 0;
	audio.src = dir_url + '/' + encodeURIComponent(playlist_name) + '/' + encodeURIComponent(playlist_data.tracks[n].file);
	audio.play();
}

function start() {
	$('#load').css('display', 'none');
	$('#app').css('display', 'block');
	$('#title').text(playlist_data.name);
	$('#download').click(function() {
		location.href = dir_url + '/' + encodeURIComponent(playlist_name) + '/playlist.zip';
	});
	play_track(current_track);
}

function next_track() {
	if (current_track != playlist_data.tracks.length - 1) {
		play_track(current_track + 1);
	}
}

function prev_track() {
	if (current_track != 0) {
		play_track(current_track - 1);
	}
}

function track_finished() {
	if ($('#autoplay')[0].checked) {
		next_track();
	}
}

function load_playlist(name, start_track) {
	playlist_name = name;
	current_track = start_track;
	set_url();

	// why.
	var script = document.createElement('script');
	script.onerror = function () {
		alert("Could not load playlist!");
	};
	script.src = dir_url + '/' + encodeURIComponent(playlist_name) + '/manifest.js';
	document.body.appendChild(script);

	// WHY.
	var id = setInterval(function () {
		if (playlist_data) {
			clearInterval(id);
			start();
		}
	}, 100);
}


$(document).ready(function () {
	var fragment = parse_fragments();
	var start = fragment['track'] || 0;
	if ('playlist' in fragment) {
		$('#load_name').val(fragment['playlist']);
		load_playlist(fragment['playlist'], Number(start));
	}

	$('#load_form').submit(function (e) {
		e.preventDefault();
		load_playlist($('#load_name').val(), 0);
	});

	$('#goodstuff').on('ended', function () {
		track_finished();
	});

	$('#arrow-left').click(prev_track);
	$('#arrow-right').click(next_track);
});
