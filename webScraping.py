import bs4 as bs
import requests

import re

import json

import youtube_dl
from youtube_title_parse import get_artist_title

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotify_credentials import spotify_client_id, spotify_client_secret, spotify_redirect_uri

import spotipy.util as util

class Automate:
    def __init__(self):
        self.url = input("Please input valid YouTube playlist url. View the full playlist and copy the url from there: ")
        self.url_id = self.get_playlist_url()
        self.songs = {}

    def get_playlist_url(self):
        id = self.url[self.url.find("=") + 1:]
        return id

    def featuring_artists(self, song):
        artists_in_song = []
        if ", " in song:
            features = song.split(", ")
            if "& " in features[len(features) - 1]:
                features[len(features) - 1] = song[song.index("&") + 2:]
            artists_in_song = [x.lower() for x in features]
        elif "&" in song:
            artists_in_song = [j.lower() for j in song.split(" & ")]
        else:
            if song[len(song) - 1] == ' ':
                artists_in_song = [song[:len(song) - 1].lower()]
            else:
                artists_in_song = [song.lower()]

        for a in range(len(artists_in_song)):
            if " of " in artists_in_song[a]:
                temp = artists_in_song[a]
                artists_in_song[a] = temp[0: temp.index(" of ")]
                artists_in_song.append(temp[temp.index(" of ") + 4:])
        return artists_in_song

    def get_artists_and_title(self, title):
        a, t = get_artist_title(title)
        artists = []

        # Get the artists from the left side of the " – "
        if "&" in a:
            if "feat" not in a and "ft" not in a and ", " not in a:
                artists = [i.lower() for i in a.split(" & ")]

        if "feat" in a:
            artists.append(a[0: a.index(" feat")].lower())
            if " feat." in a:
                others = a[a.index("feat.") + 6:]
            else:
                others = a[a.index("feat") + 5:]
            artists.extend(self.featuring_artists(others))

        elif " ft" in a:
            artists.append(a[0: a.index(" ft")].lower())
            if " ft." in a:
                others = a[a.index("ft.") + 4:]
            else:
                others = a[a.index(" ft") + 3:]
            artists.extend(self.featuring_artists(others))

        elif "," in a:
            artists.extend(self.featuring_artists(a))

        elif " x " in a:
            artists = [u.lower() for u in a.split(" x ")]

        elif "&" not in a:
            artists.append(a.lower())

        # Get the artists from the right side of the " – "
        if "*" in t:
            t = t[0: t.index("*") - 1]
        if "(" in t:
            p_string = t[t.index("(") + 1: t.index(")")]
            if "feat" in p_string:
                if "feat." in p_string:
                    others = p_string[p_string.index("feat.") + 6:]
                else:
                    others = p_string[p_string.index("feat") + 5:]
                artists.extend(self.featuring_artists(others))

            elif "Remix" in p_string:
                if p_string.lower() != "remix":
                    artists.append(p_string[0: p_string.index("Remix") - 1].lower())

            elif "ft" in p_string:

                if "ft." in p_string:
                    others = p_string[p_string.index("ft.") + 4:]
                else:
                    others = p_string[p_string.index("ft") + 3:]
                artists.extend(self.featuring_artists(others))

            elif "with" in p_string:
                others = p_string[p_string.index("with") + 5:]
                artists.extend(self.featuring_artists(others))

            try:
                t = t[0:t.index("(") - 1] + " " + t[t.index(")") + 2:]
            except (IndexError, ValueError):
                t = t[0:t.index("(") - 1]

        if " ft" in t:
            if "ft." in t:
                others = t[t.index("ft.") + 4:]
            else:
                others = t[t.index(" ft") + 3:]
            artists.extend(self.featuring_artists(others))
            t = t[0:t.index(" ft")]

        elif " feat" in t:
            if " feat." in t:
                others = t[t.index("feat.") + 6:]
            else:
                others = t[t.index("feat") + 5:]
            artists.extend(self.featuring_artists(others))
            t = t[0:t.index("feat") - 1]

        # Sometimes, the featuring artist is removed from the title from the get_artist_title() method, so this accounts for artists that were featuring, but not in t.
        original_title = self.clean_title(title)
        artists_not_caught = []
        if " ft" in original_title:
            if " ft." in original_title:
                f_artists = original_title[original_title.index("ft.") + 4:]
            else:
                f_artists = original_title[original_title.index(" ft") + 3:]
            artists_not_caught.extend(self.featuring_artists(f_artists))

        elif " feat" in original_title:
            if " feat." in t:
                f_artists = original_title[original_title.index("feat.") + 6:]
            else:
                f_artists = original_title[original_title.index("feat") + 5:]
            artists_not_caught.extend(self.featuring_artists(f_artists))

        elif "with" in original_title:
            f_artists = original_title[original_title.index("with") + 5:]
            artists_not_caught.extend(self.featuring_artists(f_artists))

        for o in artists_not_caught:
            if o not in artists:
                artists.append(o)

        if len(artists) == 3 and artists[-1] == artists[-2]:
            del artists[len(artists) - 1]



        return (artists, t)

    def get_songs(self):
        next = True

        nextPageToken = ""

        count = 0
        while next:
            if nextPageToken == "":
                r = requests.get("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=60&playlistId="
                    + self.url_id + "&key=AIzaSyCVAlxApbZiO33jD0P8URstpcfW3b_DkSw")
            else:
                r = requests.get("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=60&playlistId="
                    + self.url_id + "&key=AIzaSyCVAlxApbZiO33jD0P8URstpcfW3b_DkSw&pageToken=" + nextPageToken)
            data = r.json()

            for item in data["items"]:
                s_title = item["snippet"]["title"]
                if get_artist_title(s_title) != None:
                    all_artists, song = self.get_artists_and_title(s_title)
                    self.songs[song.lower()] = all_artists

            if "nextPageToken" not in data:
                next = False
            else:
                nextPageToken = data["nextPageToken"]
        print(self.songs)
        return self.songs

    def create_playlist(self):
        scope = 'playlist-modify-public'

        user_id = input('Enter Spotify username: ')
        token = util.prompt_for_user_token(user_id, scope, spotify_client_id, spotify_client_secret, spotify_redirect_uri)
        not_found = []
        if token:
            sp = spotipy.Spotify(auth=token)
            playlist = sp.user_playlist_create(user_id, input("Enter playlist title: "))
            song_uri_list = []
            for keys in self.songs:
                song_uri = self.search_for_song(keys, self.songs[keys], sp)
                if song_uri != '':
                    song_uri_list.append(song_uri)
                else:
                    # If song not found, verify that the artists are spelled correctly. Then try again. If it doesn't work again, try it this way. Otherwise, don't add.
                    song_uri = self.search_for_song(self.songs[keys][0] + " " + keys, self.songs[keys], sp)
                    if song_uri != '':
                        song_uri_list.append(song_uri)
                    else:
                        not_found.append(keys)

            sp.user_playlist_add_tracks(user_id, playlist['id'], song_uri_list)
            if len(not_found) != 0:
                for s in not_found:
                    print(s)
                # print(song_uri)
                # print(keys[0] + ": " + keys[1] + " " + song_uri)
                # if song_uri is None:
                #     count += 1
                # else:
                #     song_uri_list.append(song_uri)
            # print(song_uri)
            '''if len(song_uri_list) > 100:
                divisible = int(len(song_uri_list) / 100)
                remainder = len(song_uri_list) % 100

                for i in range(1, divisible + 1):
                    if i == 1:
                        self.add_song(user_id, playlist['id'], song_uri_list[0: 100], sp)
                    else:
                        self.add_song(user_id, playlist['id'], song_uri_list[(i - 1) * 100: i * 100], sp)

                self.add_song(user_id, playlist['id'], song_uri_list[divisible * 100: len(song_uri_list)], sp)
            else:
                self.add_song(user_id, playlist['id'], song_uri_list, sp)'''


            # q = 'Sam Smith'
            # song_uri = self.search_for_song(q, "How Do You Sleep?", sp)
            # self.add_song(user_id, playlist['id'], [song_uri], sp)
            # print(count)
            # return playlist
        else:
            print("Cant get token for " + user_id)
            return None
        token = ""

    def clean_title(self, search_title):
        if " - " in search_title:
            search_title = search_title[search_title.index("-") + 2:]
        if "(" in search_title:
            search_title = search_title[0: search_title.index("(") - 1]
        return search_title

    def verify_artists(self, spotify_client, list_of_artists):
        verified = []
        for a in list_of_artists:
            res = spotify_client.search(q=a, type='artist')
            verified.append(res['artists']['items'][0]['name'])
        return verified

    def search_for_song(self, song_title, song_artists, spotify_client):
        track_info = []
        results = spotify_client.search(q=song_title, type='track')
        song_uri = ''
        for i in results['tracks']['items']:
            if len(song_artists) == 2 and len(i['artists']) >= 2:
                print("both at least two")
                if i['artists'][0]['name'].lower() in song_artists and i['artists'][1]['name'].lower() in song_artists:
                    print(i['uri'])
                    song_uri = i['uri']
                    break
            elif (len(song_artists) >= 3 and len(i['artists']) >= 3):
                print("both at least three")
                same_artists_count = 0
                correct_version = False
                for x in i['artists']:
                    if x['name'].lower() in song_artists:
                        same_artists_count += 1
                    if len(song_artists) == 3 and len(i['artists']) == 3:
                        if same_artists_count >= 2:
                            print(i['uri'])
                            song_uri = i['uri']
                            correct_version = True
                            break
                    else:
                        if same_artists_count == 3:
                            print(i['uri'])
                            song_uri = i['uri']
                            correct_version = True
                            break

                if correct_version:
                    break
                """if i['artists'][0]['name'].lower() in song_artists and i['artists'][1]['name'].lower() in song_artists and i['artists'][2]['name'].lower() in song_artists:
                    print(i['uri'])
                    song_uri = i['uri']
                    break"""
            elif (len(song_artists) >= 3 and len(i['artists']) >= 2):
                print("one at least three")
                if i['artists'][0]['name'].lower() in song_artists and i['artists'][1]['name'].lower() in song_artists:
                    print(i['uri'])
                    song_uri = i['uri']
                    break
            elif len(i['artists']) == 1 and len(song_artists) == 1:
                print("both are one")
                if i['artists'][0]['name'].lower() in song_artists:
                    print(i['uri'])
                    song_uri = i['uri']
                    break



        return song_uri



        """
            returns:
            [{'external_urls': {'spotify': 'https://open.spotify.com/artist/0du5cEVh5yTK9QJze8zA0C'}, 'href': 'https://api.spotify.com/v1/artists/0du5cEVh5yTK9QJze8zA0C',
            'id': '0du5cEVh5yTK9QJze8zA0C', 'name': 'Bruno Mars', 'type': 'artist', 'uri': 'spotify:artist:0du5cEVh5yTK9QJze8zA0C'},
            {'external_urls': {'spotify': 'https://open.spotify.com/artist/4kYSro6naA4h99UJvo89HB'}, 'href': 'https://api.spotify.com/v1/artists/4kYSro6naA4h99UJvo89HB',
            'id': '4kYSro6naA4h99UJvo89HB', 'name': 'Cardi B', 'type': 'artist', 'uri': 'spotify:artist:4kYSro6naA4h99UJvo89HB'}]

            !!!!TO GET SONGS WITH MULTIPLE ARTISTS VS. THE VERSION OF THE SONG WITH ONE ARTIST!!!!
                COUNT THE NUMBER OF ARTISTS EVERYTIME THERE IS A COMMA, AMPERSAND, FEAT, FT., OR REMIX. BASED ON THAT,
                CHOOSE THE SONG WITH THAT NUMBER. HAVE THE TRACK_INFO RECORD THE NUMBER OF ARTISTS FOR THAT SONG. DONE

            artist = i['album']['artists'][0]['name']
            uri = i['uri']
            # print(artist + " " + uri)
            track_info.append((artist, uri))
        # print(track_info)
        if " " in song_artist and song_artist[len(song_artist) - 1] == " ":
            song_artist = song_artist[0: len(song_artist) - 1]

        for x in track_info:
            if x[0].lower() == song_artist.lower():
                return x[1]
                break"""

        # for i, t in enumerate(results['tracks']['items']):
        #     track_info[t['name']] = t['uri']
        # print(track_info)
        # if song_title in track_info:
        #         return track_info[song_title]


    """
    def add_song(self, user_id, playlist_id, uris, spotify_client):

        1. Print out the dictionary of all songs and titles.
        2. Search through spotify for such songs. Print out what is returned
        3. After doing so, handle the situation in which you can't find what you are looking for.
        4. (DO THIS AT THE END) If song not in spotify, then download song as mp4 and then add to spotify.

        spotify_client.user_playlist_add_tracks(user_id, playlist_id, uris)
    """

def main():
    dummy = Automate()

    dummy.get_songs()

    dummy.create_playlist()

    # Test Playlist: https://www.youtube.com/playlist?list=PLY4CekAOIcDjwx4VatbHa_rY7pV0Hs3zW

main()
