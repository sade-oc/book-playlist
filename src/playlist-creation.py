import os
import re
import json
import base64 
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-top-read playlist-modify-private playlist-modify-public ugc-image-upload"
))

# Step 1: Extract user taste (last 4 weeks)
top_tracks = sp.current_user_top_tracks(limit=20, time_range='long_term')
top_artists = sp.current_user_top_artists(limit=10, time_range='long_term')

taste_summary = {
    "top_tracks": [t['name'] for t in top_tracks['items'][:5]],
    "top_artists": [artist["name"] for artist in top_artists["items"]],
    "top_genres": list({genre for artist in top_artists["items"] for genre in artist["genres"]}),
    "avg_popularity": sum(track["popularity"] for track in top_tracks["items"]) / max(len(top_tracks["items"]), 1)
}

# Step 2: Book title
book_title = input("📚 Enter the book title (and author if possible): ").strip()

# Step 3: Build GPT prompt
prompt = f"""
You are a playlist curator. 
A user is reading the book: "{book_title}".

Their music taste summary is:
- Top Tracks: {", ".join(taste_summary['top_tracks'])}
- Top Artists: {", ".join(taste_summary['top_artists'])}
- Favorite Genres: {", ".join(taste_summary['top_genres'])}
- Average Popularity: {taste_summary['avg_popularity']}

Based on this, recommend 60 songs that match the book’s vibe 
while aligning with the user’s taste. The order/structure of 
the playlist should closely follow the book's plot and chapters. 
This is so that as the reader is reading through the book, 
the music enhances their experience and connection to the story.
The songs should prioritize reflecting the themes and emotions 
of the book over strict artist and genre alignment. This means 
that other artists and genres may be included if they better 
fit the vibe just take inspiration from the user's taste summary.

Return the results in this format:

JSON:
[
  {{ "track": "Song Title", "artist": "Artist Name" }},
  ...
]

EXPLANATION:
A short explanation of your choices and how they correlate to the theme of the book 
and the user's taste.
"""

# Step 4: Call GPT
response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7
)

output = response.choices[0].message.content

# Step 5: Extract JSON playlist
json_match = re.search(r"\[.*\]", output, re.DOTALL)
playlist = json.loads(json_match.group()) if json_match else []

# Step 6: Extract explanation
explanation_match = re.search(r"EXPLANATION:\s*(.*)", output, re.DOTALL)
explanation = explanation_match.group(1).strip() if explanation_match else "No explanation found."

# Step 7: Create Spotify playlist
user_id = sp.current_user()["id"]
playlist_name = f"📚 Reading: {book_title}"
new_playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=False, description=f"AI-curated playlist inspired by {book_title}")
playlist_id = new_playlist["id"]

print(f"Created playlist: {playlist_name}")

# >>> NEW CODE <<< Fetch book cover and upload to playlist
google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{book_title}"
res = requests.get(google_books_url).json()

if "items" in res:
    cover_url = res["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
    cover_url = cover_url.replace("zoom=1", "zoom=10")
    img_data = requests.get(cover_url).content
    image_b64 = base64.b64encode(img_data).decode("utf-8")
    sp.playlist_upload_cover_image(playlist_id, image_b64)
    print(f"✅ Uploaded book cover for '{book_title}' as playlist cover!")
else:
    print(f"⚠️ Could not find book cover for '{book_title}'.")

# Step 8: Search for tracks and add to playlist
track_ids = []
for item in playlist:
    query = f"{item['track']} {item['artist']}"
    results = sp.search(q=query, type="track", limit=1)

    if results["tracks"]["items"]:
        track_id = results["tracks"]["items"][0]["id"]
        track_ids.append(track_id)
        print(f"🎵 Found: {item['track']} by {item['artist']}")
    else:
        print(f"Not found on Spotify: {item['track']} by {item['artist']}")

if track_ids:
    for i in range(0, len(track_ids), 100):
        sp.playlist_add_items(playlist_id, track_ids[i:i+100])
    print(f"Added {len(track_ids)} tracks to playlist!")
else:
    print("No tracks were added (none found).")

# Step 9: Save explanation
os.makedirs("examples", exist_ok=True)
with open("examples/playlist_explanation.txt", "w") as f:
    f.write(explanation)

print("Explanation saved to examples/playlist_explanation.txt")
