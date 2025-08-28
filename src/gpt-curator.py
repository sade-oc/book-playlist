import os
import re
import json
import subprocess
from openai import OpenAI
from dotenv import load_dotenv

# --- Step 1: Rerun Spotify taste extraction ---

# Call the taste extraction script before using the summary
subprocess.run(["python3", "taste_extraction.py"], check=True)

# --- Step 2: Load the latest taste summary ---
with open("examples/user_taste_summary.json", "r") as f:
    taste_data = json.load(f)

taste_summary = taste_data["summary"]

# --- Step 3: GPT Playlist Prompt ---
book_title = "Long Shot by Kennedy Ryan"

prompt = f"""
You are a playlist curator. 
A user is reading the book: "{book_title}".

Their music taste summary is:
- Top Artists: {", ".join(taste_summary['top_artists'])}
- Favorite Genres: {", ".join(taste_summary['top_genres'])}
- Average Popularity: {taste_summary['avg_popularity']}

Based on this, recommend 10 songs that match the book’s vibe 
while aligning with the user’s taste. 
The songs should prioritize reflecting the themes and emotions 
of the book over strict artist and genre alignment. 
This means that other artists and genres may be included if they better fit the vibe 
just take inspiration from the user's taste summary.

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

# --- Step 4: Call GPT ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7
)

output = response.choices[0].message.content

# --- Step 5: Extract JSON playlist ---
json_match = re.search(r"\[.*\]", output, re.DOTALL)
playlist = json.loads(json_match.group()) if json_match else []

# Extract explanation
explanation_match = re.search(r"EXPLANATION:\s*(.*)", output, re.DOTALL)
explanation = explanation_match.group(1).strip() if explanation_match else "No explanation found."

# --- Step 6: Save outputs ---
os.makedirs("examples", exist_ok=True)

with open("examples/playlist_recommendations.json", "w") as f:
    json.dump(playlist, f, indent=2)

with open("examples/playlist_explanation.txt", "w") as f:
    f.write(explanation)

print("Playlist saved to examples/playlist_recommendations.json")
print("Explanation saved to examples/playlist_explanation.txt")
