"""
Step 1: Get YouTube playlist url (DONE)
Step 2: Print out song names and artist names (DONE)
Step 3: Create new playlist
Step 4: Add song to new/existing spotify playlist
Step 5: Search for song
"""


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
        self.url = ""
        self.url_id = ""
        self.songs = []

    def get_playlist_url(self):
        self.url = input("Please input YouTube playlist url: ")
        self.url_id = self.url[self.url.find("=") + 1:]
        return self.url_id

    def clean_title(self, song_title):
        if " *" in song_title:
            song_title = song_title[0: song_title.index("*") - 1]
        if "(" in song_title:
            song_title = song_title[0: song_title.index("(")]
        if "[" in song_title:
            song_title = song_title[0: song_title.index("[")]
        if "ft" in song_title:
            song_title = song_title[0: song_title.index("ft") - 1]
        elif "feat" in song_title:
            song_title = song_title[0: song_title.index("feat") - 1]
        return song_title

    def get_artist_name(self, artist="", url=""):
        artist_name = artist
        if artist_name == "" and url != "":
            video_info = youtube_dl.YoutubeDL({}).extract_info(
                url, download=False)
            artist_name = video_info["uploader"]

        if " - " in artist_name:
            artist_name = artist_name[0: artist_name.index("-") - 1]

        if "VEVO" in artist_name:
            artist_name = artist_name[0: artist_name.index("VEVO")]

        if "&" in artist_name:
            artist_name = artist_name[0: artist_name.index("&")]
        if "," in artist_name:
            artist_name = artist_name[0: artist_name.index(",")]
        elif " feat" in artist_name:
            artist_name = artist_name[0: artist_name.index("feat") - 1]
        elif " ft" in artist_name:
            artist_name = artist_name[0: artist_name.index("ft") - 1]
        elif " x " in artist_name:
            artist_name = artist_name[0: artist_name.index("x") - 1]

        if " " in artist_name and artist_name.index(" ") == len(artist_name) - 1:
            artist_name = artist_name[0: len(artist_name) - 1]

        if " " not in artist_name:
            if any(l.isupper() for l in artist_name) is False:
                split_list = [s for s in re.split("([A-Z][^A-Z]*)", artist_name) if s]
                artist_name = " ".join(split_list)

        return artist_name

    def get_songs(self):
        next = True

        nextPageToken = ""

        titles = []
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
                    artist, title = get_artist_title(s_title)
                    title = self.clean_title(title)
                    if title.lower() == "Why Don't We".lower():
                        temp = artist
                        artist = title
                        title = temp
                    artist = self.get_artist_name(artist, "")
                    # print(artist + ": " + self.clean_title(title))
                    self.songs.append((artist, self.clean_title(title)))
                else:
                    vid_id = item["snippet"]["resourceId"]["videoId"]
                    vid_url = "https://www.youtube.com/watch?v={}".format(vid_id)
                    artist = self.get_artist_name("", vid_url)
                    self.songs.append((artist, self.clean_title(s_title)))
                    # self.songs[artist] = "{}, {}".format(self.clean_title(s_title), vid_url)
                    # print(self.songs[artist] + " " + artist)
                count += 1



            if "nextPageToken" not in data:
                next = False
            else:
                nextPageToken = data["nextPageToken"]
        print(count)
        print(len(self.songs))
        return self.songs

    """
    def get_song(self):
        vid_url = input("Give video url: ")
        self.get_artist_name(vid_url)
    """

    def create_playlist(self):
        scope = 'playlist-modify-public'

        user_id = input('Enter Spotify username: ')
        token = util.prompt_for_user_token(user_id, scope, spotify_client_id, spotify_client_secret, spotify_redirect_uri)
        if token:
            sp = spotipy.Spotify(auth=token)
            playlist = sp.user_playlist_create(user_id, input("Enter playlist title: "))
            song_uri_list = []
            # print(self.search_for_song("Dua Lipa", "Don't Start Now", sp))
            count = 0
            for keys in self.songs:
                song_uri = self.search_for_song(keys[0], keys[1], sp)
                # print(song_uri)
                # print(keys[0] + ": " + keys[1] + " " + song_uri)
                if song_uri is None:
                    count += 1
                else:
                    song_uri_list.append(song_uri)
            # print(song_uri)
            if len(song_uri_list) >= 100:
                divisible = int(len(song_uri_list) / 100)
                remainder = len(song_uri_list) % 100
            for i in range(1, divisible + 1):
                if i == 1:
                    self.add_song(user_id, playlist['id'], song_uri_list[0: 100], sp)
                else:
                    self.add_song(user_id, playlist['id'], song_uri_list[(i - 1) * 100: i * 100], sp)

            self.add_song(user_id, playlist['id'], song_uri_list[divisible * 100: len(song_uri_list)], sp)


            # q = 'Sam Smith'
            # song_uri = self.search_for_song(q, "How Do You Sleep?", sp)
            # self.add_song(user_id, playlist['id'], [song_uri], sp)
            print(count)
            return playlist
        else:
            print("Cant get token for " + user_id)
            return None
        token = ""

    def search_for_song(self, song_artist, song_title, spotify_client):
        """
        1. Clean the title up
        2. If the song is there, then return the song identifier in spotify
        3. If the song is not there, then return 'SONG NOT FOUND', and return the song title.
           Ask the user to retype the song name and artist name to search for the song again.

           NOTE: USE A CURL REQUEST. SEE PREVIOUS GITHUBS FOR HOW TO DO IT.
        """
        track_info = []
        results = spotify_client.search(q=song_title, type='track')
        # print(results['tracks']['items'])
        for i in results['tracks']['items']:
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
                break
        # for i, t in enumerate(results['tracks']['items']):
        #     track_info[t['name']] = t['uri']
        # print(track_info)
        # if song_title in track_info:
        #         return track_info[song_title]


    def add_song(self, user_id, playlist_id, uris, spotify_client):
        """
        1. Print out the dictionary of all songs and titles.
        2. Search through spotify for such songs. Print out what is returned
        3. After doing so, handle the situation in which you can't find what you are looking for.
        4. (DO THIS AT THE END) If song not in spotify, then download song as mp4 and then add to spotify.
        """
        spotify_client.user_playlist_add_tracks(user_id, playlist_id, uris)

def main():
    dummy = Automate()

    # print(dummy.clean_title("Perfect Life ft. Sean Terrio"))

    url = dummy.get_playlist_url()

    i = dummy.get_songs()

    # count = 0
    # for keys in i:
    #     print(keys + ": " + i[keys])
    #     count+=1
    # print(count)

    pl = dummy.create_playlist()
    if pl != None:
        print(pl["id"])

main()
