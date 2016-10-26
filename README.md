# mixtape

Last weekend I was really emotional and sitting on a plane for a huge number of hours, so I started designing playlists for all my friends.
The problem is that I use a streaming music service that pretty much nobody else does, so I have basically no way to share those playlists with anybody else, short of just sending them a list of title and telling them to put it together themselves!

How do you make a mixtape in 2016?

Well, you rip the songs from youtube and then host them somewhere on the internet, I guess.
That's what I did, at least.

## Web interface

`index.html`, `script.js`, and `style.css` should be dumped into a folder somewhere on some webserver. That's all you need to get started.
If you want to, the webpage works fine just opening `index.html` in a web browser from your filesystem.
Then, in order to make playlists usable from it, you just put a playlist folder into the same folder as `index.html`.
How do you make a playlist folder? That's what `assemble.py` does.
Run it and it'll walk you through putting together the playlist, letting you enter metadata for the song and then chosing a source for the audio file, which can be anything from picking a local file to automatically finding the song on youtube for you.
Really, a playlist folder is just a folder with a `manifest.json` file and then all the audio files you want to use, but the script makes this incredibly easy.

If at any point the creation process gets interrupted, you can pick up where you left off.

## Dependencies

`$ pip install bs4 youtube-dl`
`$ sudo apt-get install python-tk`

## TODOs

- Add "download all" functionality
- Make the webpage look better on mobile
- Add keyboard shortcuts
