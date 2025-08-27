import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd
import json

# Load credentials
load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-top-read"
))

# Get user's top tracks
top_tracks = sp.current_user_top_tracks(limit=20, time_range='medium_term')  # last 6 months

tracks_data = []
artist_cache = {}  # cache for artist genres

for t in top_tracks['items']:
    artist_id = t['artists'][0]['id']
    if artist_id not in artist_cache:
        artist_cache[artist_id] = sp.artist(artist_id).get('genres', [])

    track_info = {
        'name': t['name'],
        'artist': t['artists'][0]['name'],
        'id': t['id'],
        'popularity': t['popularity'],
        'genres': ", ".join(artist_cache[artist_id]),  # convert list to string for CSV
        'album': t['album']['name'],
        'release_date': t['album']['release_date'],
        'explicit': t['explicit'],
        'duration_ms': t['duration_ms']
    }
    tracks_data.append(track_info)

# Collect track IDs
track_ids = [t['id'] for t in tracks_data if t['id'] is not None]
print("🎵 Collected track IDs:", track_ids)

# Fetch top artists + genres
top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')
genres = [g for artist in top_artists['items'] for g in artist.get('genres', [])]
unique_genres = list(dict.fromkeys(genres))

taste_summary = {
    "top_artists": [artist['name'] for artist in top_artists['items']],
    "top_genres": unique_genres[:5],
    "avg_popularity": round(sum(t['popularity'] for t in top_tracks['items']) / len(top_tracks['items']), 2),
}

# Save as CSV
os.makedirs("examples", exist_ok=True)
df = pd.DataFrame(tracks_data)
df.to_csv("examples/user_top_tracks.csv", index=False)

# Save as JSON for GPT usage
with open("examples/user_taste_summary.json", "w") as f:
    json.dump({
        "tracks": tracks_data,
        "summary": taste_summary
    }, f, indent=2)

print("\nUser music taste extracted to examples/user_top_tracks.csv")
print("\nTaste summary:")
print("Top artists:", ", ".join(taste_summary['top_artists']))
print("Top genres:", ", ".join(taste_summary['top_genres']))
print("Average popularity:", taste_summary['avg_popularity'])
