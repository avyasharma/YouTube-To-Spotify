"""
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id='e4db7c20caa54bc2b44eb7b789ac72eb', client_secret='843199c7c4174cf7829db1218ad302b6', redirect_uri='https://localhost:8080', cache_path='.youtubetospotifycache'))
user_id = 'avi.sharma'

body = json.dumps({
    "name": "Youtube Liked Vids",
    "description": "All Liked Youtube Videos",
    "public": True
})

query = "https://api.spotify.com/v1/users/{}/playlists".format(
    spotify_user_id)
response = requests.post(
    query,
    data=request_body,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(spotify_token)
    }
)
response_json = response.json()

# playlist id
return response_json["id"]
"""
