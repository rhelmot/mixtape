#!/usr/bin/env python

import os
import sys
import youtube_dl
import requests
import urllib
import json
from bs4 import BeautifulSoup
import subprocess
import eyed3
import random
import shutil

from Tkinter import Tk
from tkFileDialog import askopenfilename

Tk().withdraw()

TMP_FILE = '/tmp/mixtape_int'

class Playlist(object):
    def __init__(self, ident, name, tracks=None):
        self.id = ident
        self.name = name
        self.tracks = [] if tracks is None else tracks

    PREAMBLE = 'var playlist_data = '

    @classmethod
    def create(cls, ident, name):
        os.mkdir(ident)
        return cls(ident, name)

    @classmethod
    def load(cls, ident):
        with open(os.path.join(ident, 'manifest.js')) as f:
            f.read(len(cls.PREAMBLE))
            return cls.from_dict(ident, json.load(f))

    def save_manifest(self):
        with open(os.path.join(self.id, 'manifest.js'), 'w') as f:
            f.write(self.PREAMBLE)
            json.dump(self.as_dict, f, sort_keys=True, indent=4, separators=(',', ': '))

    def save_zip(self):
        zipfile = '%s/playlist.zip' % (self.id,)
        globs = '%s/*.mp3' % (self.id,)
        if os.path.exists(zipfile):
            os.unlink(zipfile)
        if os.system('zip %s %s' % (zipfile, globs)) != 0:
            print 'Zip creation failed...'

    @property
    def as_dict(self):
        return {
            'name': self.name,
            'tracks': [x.as_dict for x in self.tracks],
        }

    @classmethod
    def from_dict(cls, ident, d):
        name = d['name']
        self = cls(ident, name)
        self.tracks = [Track.from_dict(self, x) for x in d['tracks']]
        return self

    def menu_loop(self):
        while True:
            try:
                if not self.menu():
                    break
            except KeyboardInterrupt:
                pass

        self.finalize()

    def menu(self):
        print '1. Add track'
        print '2. Remove track'
        print '3. Edit track'
        print '4. Move tracks'
        print '5. Done'

        choice = ''
        while choice not in ('1', '2', '3', '4', '5'):
            choice = raw_input('> ')

        if choice == '1':
            track = Track.menu_create(self)
            if track is not None:
                self.tracks.append(track)

        elif choice == '2':
            tid = self.menu_select_track()
            self.tracks.pop(tid)

        elif choice == '3':
            tid = self.menu_select_track()
            self.tracks[tid].menu_edit()

        elif choice == '4':
            tid1 = self.menu_select_track('Move what?\n> ')
            tid2 = self.menu_select_track('Move where?\n> ')
            self.tracks.insert(tid2, self.tracks.pop(tid1))

        elif choice == '5':
            return False
        return True

    def show_tracks(self):
        for i, track in enumerate(self.tracks):
            print '%02d. %s - %s' % (i + 1, track.title, track.artist)

    def menu_select_track(self, prompt='> '):
        self.show_tracks()

        while True:
            choice = raw_input(prompt)
            try:
                choice = int(choice)
                choice -= 1
                if 0 <= choice < len(self.tracks):
                    return choice
            except ValueError:
                pass

    def finalize(self):
        for i, track in enumerate(self.tracks):
            track.finalize(i + 1)
        self.save_manifest()
        self.save_zip()


class Track(object):
    def __init__(self, playlist, title, artist, fname, album=None, description=''):
        self.playlist = playlist
        self.title = title
        self.artist = artist
        self.album = album
        self.file = fname
        self.description = description

    @property
    def file_path(self):
        return os.path.join(self.playlist.id, self.file)

    @property
    def as_dict(self):
        return {
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'description': self.description,
            'file': self.file
        }

    @classmethod
    def from_dict(cls, playlist, d):
        try:
            return cls(playlist, d['title'], d['artist'], d['file'], d['album'], d['description'])
        except KeyError:
            return cls(playlist, d['name'], d['artist'], d['file'], '', d['description'])

    @classmethod
    def menu_create(cls, playlist):
        track = cls(playlist, None, None, None)
        track.menu_select_file()
        track.extract_metadata()
        track.menu_fill_metadata()
        return track

    def menu_select_file(self):
        while True:
            try:
                in_fname = self.menu_select_file_inner()
            except KeyboardInterrupt:
                continue
            else:
                if in_fname is None:
                    raise KeyboardInterrupt

                if self.apply_audio(in_fname):
                    break

    def apply_audio(self, in_fname):
        rfile = '%s.mp3' % ''.join(random.choice('0123456789abcdef') for _ in xrange(8))
        if not convert_audio(in_fname, os.path.join(self.playlist.id, rfile)):
            return False

        self.file = rfile
        if sys.platform != 'win32':
            os.chmod(self.file_path, 0664)
        return True

    def extract_metadata(self):
        meta = eyed3.load(self.file_path)
        if meta.tag is not None:
            if self.title is None and meta.tag.title is not None:
                self.title = meta.tag.title.encode('utf-8')
            if self.artist is None and meta.tag.artist is not None:
                self.artist = meta.tag.title.encode('utf-8')
            if self.album is None and meta.tag.album is not None:
                self.album = meta.tag.album.encode('utf-8')

    def menu_fill_metadata(self):
        if self.title is None: self.title = raw_input('Title: ')
        if self.artist is None: self.artist = raw_input('Artist: ')
        if self.album is None: self.album = raw_input('Album: ')

    def show(self):
        print self.title
        print self.artist, '-', self.album
        print 'Description:'
        print self.description
        print

    def menu_edit(self):
        self.show()
        while self.menu_edit_inner():
            pass

    def menu_edit_inner(self):
        print '1. Title'
        print '2. Artist'
        print '3. Album'
        print '4. Description'
        print '5. File'
        print '6. Done'

        choice = ''
        while choice not in ('1', '2', '3', '4', '5', '6'):
            choice = raw_input('> ')

        if choice == '1':
            self.title = raw_input('Title: ')
        elif choice == '2':
            self.artist = raw_input('Artist: ')
        elif choice == '3':
            self.album = raw_input('Album: ')
        elif choice == '4':
            self.menu_set_description()
        elif choice == '5':
            self.menu_select_file()
        elif choice == '6':
            return False
        return True

    def finalize(self, num):
        new_file = '%02d - %s.mp3' % (num, self.title)
        if new_file != self.file:
            old_path = self.file_path
            self.file = new_file
            shutil.move(old_path, self.file_path)

        meta = eyed3.load(self.file_path)
        if meta.tag is None or meta.tag.version < (2, 3, 0):
            meta.initTag()
        meta.tag.title = self.title.decode('utf-8')
        meta.tag.artist = self.artist.decode('utf-8')
        meta.tag.album = self.album.decode('utf-8')
        meta.tag.save()

    def menu_select_file_inner(self):
        print 'How do you want to find an audio file?'
        print '1) Search youtube'
        print '2) Browse for file'
        print '3) Enter youtube url'
        print '4) Enter audio URL'
        print '5) Never mind'

        how = ''
        while how not in ('1', '2', '3', '4', '5'):
            how = raw_input('> ')

        if how == '1':
            # bootstrap
            self.menu_fill_metadata()

            print 'Searching youtube...'
            possible_url = None
            for possible_url in yt_search(self.artist + ' ' + self.title):
                with youtube_dl.YoutubeDL({'noplaylist': True}) as ydl:
                    try:
                        metadata = ydl.extract_info(possible_url, download=False)
                        print metadata['title']
                        print possible_url
                        use = ''
                        while use not in ('y', 'n'):
                            use = raw_input('Use this video? y/n ')

                        if use == 'y':
                            break
                    except youtube_dl.utils.DownloadError:
                        print 'Download error...'
                        raise KeyboardInterrupt
            else:
                print 'Exhausted search...'
                raise KeyboardInterrupt

            return yt_download(possible_url)

        elif how == '2':
            url = askopenfilename()
            try:
                if not os.path.exists(url):
                    raise KeyboardInterrupt
            except TypeError:
                raise KeyboardInterrupt

            return url

        elif how == '3':
            url = raw_input('Enter URL: ')
            return yt_download(url)

        elif how == '4':
            url = raw_input('Enter URL: ')

            print 'Downloading...'
            with open(TMP_FILE, 'wb') as f:
                f.write(requests.get(url).content)
            print 'Downloaded!'
            return url

        elif how == '5':
            return None

        else:
            raise KeyboardInterrupt

    def menu_set_description(self):
        print 'Enter track description. Type DONE by itself on a line when you are done.'
        descr = []
        while True:
            line = raw_input('')
            if line == 'DONE':
                break
            else:
                descr.append(line)
        self.description = '\n'.join(descr)


def yt_search(query):
    query = urllib.quote(query)
    url = "https://www.youtube.com/results?search_query=" + query
    html = requests.get(url).content
    soup = BeautifulSoup(html)
    for vid in soup.findAll(attrs={'class':'yt-uix-tile-link'}):
        yield 'https://www.youtube.com' + vid['href']

def yt_download(url):
    with youtube_dl.YoutubeDL({
        'format': 'bestaudio',
        'noplaylist': True,
        'outtmpl': TMP_FILE,
        }) as ydl:

        try:
            #metadata = ydl.extract_info(url, download=False)
            ydl.download([url])
            return TMP_FILE
        except youtube_dl.utils.DownloadError:
            print 'Download failed somehow?????'
            raise KeyboardInterrupt

def convert_audio(in_fname, out_fname):
    if subprocess.call(['ffmpeg', '-i', in_fname, out_fname]) != 0:
        print 'Conversion failed...'
        return False
    return True

def validate_playlist_id(s):
    if len(s) == 0:
        return False

    for c in s:
        if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0987654321-_.,':
            continue
        else:
            return False

    return True

def migrate(playlist):
    has_any = False
    for track in playlist.tracks:
        if not track.file.endswith('.mp3'):
            track.apply_audio(track.file_path)
            has_any = True
    if has_any:
        playlist.finalize()

def main():
    if len(sys.argv) > 1:
        playlist_id = sys.argv[1]
    else:
        playlist_id = ''

    while not validate_playlist_id(playlist_id):
        playlist_id = raw_input('Enter playlist identifier (no spaces or special chars): ')

    if not os.path.exists(playlist_id):
        print 'Creating new playlist...'
        name = raw_input('Enter playlist name: ')
        playlist = Playlist.create(playlist_id, name)
    else:
        playlist = Playlist.load(playlist_id)
        migrate(playlist)
        print 'Resuming playlist "%s"' % playlist.name

    playlist.menu_loop()

if __name__ == '__main__':
    main()
