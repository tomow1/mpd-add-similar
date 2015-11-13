#       
#       Copyright 2009 Amr Hassan <amr.hassan@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.


import mpd, pylast, random, os

###
### A Track is represented as a dictionary holding all the track attributes, with
### the simplist being a {"artist": ..., "title": ...} track.
###

def Track(artist, title, **kwargs):
    """
        Returns a dictionary Track
    """
    
    d = {"artist": artist, "title": title}
    for k in kwargs:
        d[k] = kwargs[k]
    
    return d

_lastfm = pylast.get_lastfm_network(api_key="dfa3901334ad611f9c298cd9a2501156", api_secret="fc74834154a00f641e75417c08819884")
_mpd_client = mpd.MPDClient()

# Guess default values
try:
    _MPD_HOST = os.environ["MPD_HOST"]
except KeyError:
    _MPD_HOST = "localhost"

try:
    _MPD_PORT = int(os.environ["MPD_PORT"])
except KeyError:
    _MPD_PORT = 6600


def mpd_connect(host=_MPD_HOST, port=_MPD_PORT):
    """
        Connect to a MPD server
    """
    
    _mpd_client.connect(host, port)

def _get_similar_tracks(track):
    """
        Returns a sequence of tracks
    """
    
    l = []
    for track in _lastfm.get_track(track["artist"], track["title"]).get_similar():
        track = track.item
        l.append({"artist": track.get_artist().get_name(), "title": track.get_title()})
    
    return l

def _get_similar_artists(artist):
    """
        Returns a sequence of artists
    """

    l = []
    for artist in _lastfm.get_artist(artist).get_similar():
        artist = artist.item
        l.append(artist.get_name())

    return l

def _get_top_tracks(artist, limit):
    """
        Returns a sequence of tracks
    """

    l = []
    for track in _lastfm.get_artist(artist).get_top_tracks(limit=limit):
        track = track.item
        l.append({"artist": track.get_artist().get_name(), "title": track.get_title()})
    
    return l

def _mpd_lookup_track(track):
    """
        Returns a sequence of MPD URIs
    """
    
    args = ["artist", track["artist"].encode("utf-8"), "title", track["title"].encode("utf-8")]
    hits = []
    
    for match in _mpd_client.find(*args) + _mpd_client.search(*args):
        hits.append(match["file"])
    
    return hits

def _mpd_lookup_artist_tracks(artist):
    """
        Returns a sequence of MPD URIs
    """

    args = ["artist", artist.encode("utf-8")]
    hits = []

    for match in _mpd_client.search(*args):
        hits.append(match["file"])

    return hits

def _mpd_get_playlist(position=None):
    """
        Returns the current tracks on MPD's playlist
    """
    
    if position != None:
        return _mpd_client.playlistinfo(position)
    else:
        return _mpd_client.playlistinfo()

def _is_track_added(uri):
    """ Pretty self-explanatory """
    
    for track in _mpd_get_playlist():
        if track["file"] == uri:
            return True
    
    return False

def _mpd_add_track(uri, position = None):
    """
        Add a URI of a track to the current playlist
    """
    
    if position != None:
        _mpd_client.addid(uri, position)
    else:
        _mpd_client.addid(uri)

def get_playlist_length():
    """
        Returns the length of MPD's current playlist
    """
    
    return len(_mpd_get_playlist())

def _mpd_current_playlist_position():
    return _mpd_client.status()["song"]

def add_similar_tracks(position_or_range = ":", howmany=5, relative_positions=True):
    """
        Adds Up to the value of howmany tracks similar to
        each track on the current playlist.
        
        parameters:
        ===========
            # position_or_range: The position of the track to add similar tracks 
                to. Can also be a range string as "START:STOP" with the STOP
                position not included, acceptable ranges include empty START and/or empty
                STOP values for the first and last values in the playlist. The character
                "c" can be used to indicate the current playing posision. Example:
                    ":" for all tracks
                    ":-3" for all but the last three tracks
                    "c:" for the current playing song and the rest following it
            # howmany: Maximum number of added similar tracks
                per existing track
            # relative_position: Whether to add similar tracks after
                their respective original track (True) or at the end
                of the playlist (False)
        
        Returns the number of added tracks
    """
    
    # Handle the range case
    if type(position_or_range) == str and ":" in position_or_range:
        (start, stop) = position_or_range.split(":")
        
        if start == "": start = 0
        if stop == "": stop = get_playlist_length()
        if start == "c": start = _mpd_current_playlist_position()
        if stop == "c": stop = _mpd_current_playlist_position()
        
        (start, stop) = (int(start), int(stop))
        
        if stop < 0:
            stop = get_playlist_length + stop
        
        added = 0
        for i in xrange(start, stop):
            if relative_positions:
                added += add_similar_tracks(i+added, howmany, True)
            else:
                added += add_similar_tracks(i, howmany, False)
        
        return added
    
    
    # Handle the single position case
    added = 0
    relative_buffer = {}
    normal_buffer = []
    if position_or_range == "c":
        position = int(_mpd_current_playlist_position())
    else:
        position = int(position_or_range)
        
    # Get similar tracks' URIs
    for track in _get_similar_tracks(_mpd_get_playlist(position)[0]):
        
        if added >= howmany: break
        
        # look up track
        uris = _mpd_lookup_track(track)
        if not uris: continue
        
        # check to see if it's already added
        uri = uris[0]
        if _is_track_added(uri): continue
        
        # add it to the buffer
        if relative_positions:
            relative_buffer[position+added+1] = uri
        else:
            normal_buffer += [uri]
        added += 1
    
    if added < howmany:
        
        print added
        artist = _mpd_get_playlist(position)[0]["artist"]
        artists = [artist]
        artists.extend(_get_similar_artists(artist))
        
        songs = []
        for a in artists:
            uris = _mpd_lookup_artist_tracks(artist)
            songs.extend(uris)
        
        random.shuffle(songs)
        
        for song in songs:
            if added >= howmany: break
            # check to see if it's already added
            if _is_track_added(song): continue
            # add it to the buffer
            if relative_positions:
                relative_buffer[position+added+1] = song
            else:
                normal_buffer += [song]
            added += 1
        
        print added
    
    # add tracks from buffer
    _mpd_client.command_list_ok_begin()

    if relative_positions:
        keys = relative_buffer.keys()
        keys.sort()
        for key in keys:
            _mpd_add_track(relative_buffer[key], key)
    else:
        for uri in normal_buffer:
            _mpd_add_track(uri)
    
    _mpd_client.command_list_end()
    
    return added

def add_top_tracks(artist, howmany=15, relative_positions=True):
    print artist
    added = 0
    relative_buffer = {}
    normal_buffer = []
    position = 0
    if relative_positions:
        position = _mpd_current_playlist_position()
    else:
        position = get_playlist_length()
        
    for track in _get_top_tracks(artist, howmany*2):
	print track
        
        if added >= howmany: break
        
        # look up track
        uris = _mpd_lookup_track(track)
        if not uris: continue
        
        # check to see if it's already added
        uri = uris[0]
        if _is_track_added(uri): continue
        
        # add it to the buffer
        if relative_positions:
            relative_buffer[position+added+1] = uri
        else:
            normal_buffer += [uri]
        
        added += 1

    # add tracks from buffer
    _mpd_client.command_list_ok_begin()

    if relative_positions:
        keys = relative_buffer.keys()
        keys.sort()
        for key in keys:
            _mpd_add_track(relative_buffer[key], key)
    else:
        for uri in normal_buffer:
            _mpd_add_track(uri)
    
    _mpd_client.command_list_end()
    
    return added
