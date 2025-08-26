import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Auth manager
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="playlist-modify-private"
))

# Get current user
user_id = sp.current_user()["id"]

# Create a new private playlist
playlist = sp.user_playlist_create(
    user=user_id,
    name="Book Playlist Test",
    public=False,
    description="A test playlist created via Spotipy 🚀"
)

print("Playlist created!")
print("Link:", playlist["external_urls"]["spotify"])



# Some test songs we’ll search for
songs = [
    "Blinding Lights The Weeknd",
    "Levitating Dua Lipa",
    "As It Was Harry Styles"
]

track_uris = []

for song in songs:
    results = sp.search(q=song, limit=1, type="track")
    tracks = results["tracks"]["items"]
    if tracks:
        uri = tracks[0]["uri"]
        track_uris.append(uri)
        print(f"🎵 Found: {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}")
    else:
        print(f"❌ No results for {song}")

# Add tracks to the playlist
if track_uris:
    sp.playlist_add_items(playlist_id=playlist["id"], items=track_uris)
    print("✅ Tracks added to playlist!")