import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="8cf20745c9164fc38fc928e911f7969f",
                                                           client_secret="1799a9145bd94a3895853735f7eda5dd"))

defaulturl = 'https://api.deezer.com/'

__all__ = ['parse_check']


def parse_deezer(msg):
    r = requests.get(msg)
    if 'playlist' in r.url:
        # start = r.url.find('playlist/') + len('playlist/')
        # pretext = 'playlist/'
        return False
    elif 'album' in r.url:
        # start = r.url.find('album/') + len('album/')
        # pretext = 'album/'
        return False
    elif 'track' in r.url:
        start = r.url.find('track/') + len('track/')
        pretext = 'track/'
    else:
        return False
    end = r.url.find('?utm')
    info = r.url[start:end]
    new = defaulturl + pretext + info + '&output=json'
    r = requests.get(new)
    jsson = r.json()
    if pretext == 'album/' or pretext == 'playlist/':
        result = []
        for link in jsson['tracks']['data']:
            result.append(link['artist']['name'] + link['title'])
        return result
    else:
        return jsson['artist']['name'] + ' ' + jsson['title']


def parse_spotify(msg):
    if 'track' in msg:
        results = sp.track(msg)
        artists = ''
        for artist in results['artists']:
            artists = artists + artist['name']
        return artists + results['name']
    # elif 'playlist' in msg:
    #     results = sp.playlist_items('https://open.spotify.com/playlist/4xTjQDYg6kXcXqYCgiYXhv?si=G4T6-bSsSSiqrYLJz9g6nQ', fields='items')
    #     for track in results['items']:
    #        for artist in track['track']['artists']:
    #            print(artist['name'])
    #        print(track['track']['name'])
    #    return None#results#['items']['track']['name']
    else:
        return None


def parse_check(msg):
    if 'deezer' in msg:
        res = parse_deezer(msg)
        return res
    elif 'spotify' in msg:
        res = parse_spotify(msg)
        return res
    else:
        return None
