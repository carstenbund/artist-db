import openai
import sqlite3
import json
import time

# Set your API key
client = openai.OpenAI(
        api_key="xxx",
        project="xxx")

with open("contemporary_artists.json", "r", encoding="utf-8") as f:
    ARTIST_NAMES = json.load(f)

# SQLite DB setup
conn = sqlite3.connect("artists.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS artists (
    name TEXT PRIMARY KEY,
    data TEXT
)
""")

PROMPT_TEMPLATE = """
You are a cultural analyst. Analyze the artist: "{name}".

Respond with a valid JSON object that exactly matches this structure:

- Do not include any explanation.
- Do not wrap the result in Markdown.
- Use double quotes for all keys and values.
- Respond only with the JSON.

{{
  "name": "{name}",
  "time_period": "<years of main activity or life>",
  "cultural_context": "<nation, movement, relevant socio-political context>",
  "primary_medium": ["<media used>"],
  "workflow_mode": "Engaged | Withdrawn | Hybrid",
  "attention_metrics": {{
    "societal_engagement": 1-5,
    "institutional_dependency": 1-5,
    "inner_motivation": 1-5,
    "audience_addressed": 1-5,
    "discursive_participation": 1-5,
    "visibility_in_lifetime": 1-5
  }},
  "role_identity": ["<list of tags like Mystic, Educator, etc>"],
  "narrative_context": {{
    "triggering_forces": ["<social/spiritual/political forces>"],
    "conflict_zones": ["<personal or institutional struggles>"],
    "legacy_mode": "<Canonical | Marginal | Rediscovered | etc>",
    "alignment_with_power": "<Ally | Adversary | Independent>",
    "myth_construction": "<Summary of how they were mythologized or not>"
  }}
}}
"""

# Prompt generator
def build_prompt(name):
    return PROMPT_TEMPLATE.format(name=name)

# API call
def get_artist_data(name):
    prompt = build_prompt(name)
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error for {name}: {e}")
        return None


# Insert JSON into SQLite
def save_to_db(name, data):
    cur.execute("REPLACE INTO artists (name, data) VALUES (?, ?)", (name, json.dumps(data)))
    conn.commit()

# Main loop
for name in ARTIST_NAMES:
    print(f"Processing {name}...")
    data = get_artist_data(name)
    if data:
        save_to_db(name, data)
    time.sleep(1)  # polite pause between calls

# Export to JSON (optional)
def export_all_to_json():
    cur.execute("SELECT data FROM artists")
    all_data = [json.loads(row[0]) for row in cur.fetchall()]
    with open("artist_scorecards.json", "w") as f:
        json.dump(all_data, f, indent=2)

export_all_to_json()
conn.close()

