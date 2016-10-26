#!/usr/bin/env python

import os
import youtube_dl
import requests
import shutil
import urllib
import json
from bs4 import BeautifulSoup

from Tkinter import Tk
from tkFileDialog import askopenfilename

Tk().withdraw()

yt_fmt = u"%(title)s-%(id)s.%(ext)s"

def yt_search(query):
    query = urllib.quote(query)
    url = "https://www.youtube.com/results?search_query=" + query
    html = requests.get(url).content
    soup = BeautifulSoup(html)
    for vid in soup.findAll(attrs={'class':'yt-uix-tile-link'}):
        yield 'https://www.youtube.com' + vid['href']

def yt_download(pl_id, url):
    with youtube_dl.YoutubeDL({
        'format': 'bestaudio',
        'noplaylist': True,
        'outtmpl': os.path.join(pl_id, yt_fmt)
        }) as ydl:

        try:
            metadata = ydl.extract_info(url, download=False)
            fname = yt_fmt % metadata
            if os.path.exists(os.path.join(pl_id, fname)):
                print 'Already using a file of that name!'
                return None

            ydl.download([url])
            return fname
        except youtube_dl.utils.DownloadError:
            return None

def validate(pl_id):
    if len(pl_id) == 0:
        return False

    for c in pl_id:
        if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0987654321-_.,':
            continue
        else:
            return False

    return True

def main():
    pl_id = ''
    while not validate(pl_id):
        pl_id = raw_input('Enter playlist identifier (no spaces or special chars): ')

    if os.path.exists(pl_id):
        with open(os.path.join(pl_id, 'manifest.json')) as f:
            playlist = json.load(f)
        print 'Resuming playlist "%s"' % playlist['name']
    else:
        os.mkdir(pl_id)
        playlist = {}
        playlist['name'] = raw_input('Enter playlist name: ')
        playlist['tracks'] = []

    while True:
        try:
            track = {}
            track['name'] = raw_input('Enter track name: ')
            track['artist'] = raw_input('Enter track artist: ')

            print 'Enter track description. Type DONE by itself on a line when you are done.'
            descr = []
            while True:
                line = raw_input('')
                if line == 'DONE':
                    break
                else:
                    descr.append(line)
            track['description'] = '\n'.join(descr)

            how = ''
            fname = None
            while fname is None:
                how = raw_input('How do you want to find an audio file?\n1) Search youtube\n2) Browse for file\n3) Enter youtube url\n4) Enter audio URL\n> ')

                if how == '1':
                    print 'Searching youtube...'
                    possible_url = None
                    for possible_url in yt_search(track['artist'] + ' ' + track['name']):
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
                                continue
                    else:
                        print 'Exhausted search...'
                        continue

                    fname = yt_download(pl_id, possible_url)

                elif how == '2':
                    url = askopenfilename()
                    try:
                        if not os.path.exists(url):
                            continue
                    except TypeError:
                        continue

                    if os.path.exists(os.path.join(pl_id, os.path.basename(url))):
                        print 'Already using a file of that name!'
                        continue

                    shutil.copy(url, os.path.join(pl_id, os.path.basename(url)))
                    fname = os.path.basename(url)

                elif how == '3':
                    url = raw_input('Enter URL: ')
                    fname = yt_download(pl_id, url)

                elif how == '4':
                    url = raw_input('Enter URL: ')

                    if os.path.exists(os.path.join(pl_id, os.path.basename(url))):
                        print 'Already using a file of that name!'
                        continue

                    print 'Downloading...'
                    with open(os.path.join(pl_id, os.path.basename(url)), 'wb') as f:
                        f.write(requests.get(url).content)
                    print 'Downloaded!'
                    fname = os.path.basename(url)

            track['file'] = fname

            playlist['tracks'].append(track)
        except KeyboardInterrupt:
            pass

        # save in-progress list...
        with open(os.path.join(pl_id, 'manifest.json'), 'w') as fp:
            json.dump(playlist, fp, sort_keys=True, indent=4, separators=(',', ': '))

        choice = ''
        while choice not in ('y', 'n'):
            choice = raw_input('Add more tracks? y/n ')

        if choice == 'n':
            break

    print 'Done!!!!!'

if __name__ == '__main__':
    main()
