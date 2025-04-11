
import sqlite3
import json
import time
from openai import OpenAI

# Initialize OpenAI client
# Set your API key
client = OpenAI(
        api_key="xxx",
        project="xxx")

#ASSISTANT_ID="asst_E12XXRulPDxZQdBmJBweCWfD"
ASSISTANT_ID="asst_xxy"

# Load artist names
with open("contemporary_artists.json", "r", encoding="utf-8") as f:
    ARTIST_NAMES = json.load(f)

# Artist names to analyze
#ARTIST_NAMES = ["Hilma af Klint", "Diego Rivera", "Joseph Beuys"]



# Connect to the enhanced schema SQLite DB
conn = sqlite3.connect("artist_scorecards.db")
cur = conn.cursor()


def build_prompt(name):
    return PROMPT_TEMPLATE.format(name=name)

def insert_artist_name(artist_id, name_type, name):
  cur.execute("""
    INSERT INTO artist_names (artist_id, name_type, name)
    VALUES (?, ?, ?)
  """, (artist_id, name_type, name))
    
def get_or_create_artist(name):
    cur.execute("SELECT id FROM artists WHERE canonical_name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO artists (canonical_name) VALUES (?)", (name,))
    return cur.lastrowid

def get_or_create_attribute(attr_name):
    cur.execute("SELECT id FROM attributes WHERE name = ?", (attr_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO attributes (name) VALUES (?)", (attr_name,))
    return cur.lastrowid

def insert_attribute_value(artist_id, attr_name, value):
    attr_id = get_or_create_attribute(attr_name)
    cur.execute("""
        INSERT OR REPLACE INTO artist_attributes (artist_id, attribute_id, value)
        VALUES (?, ?, ?)
    """, (artist_id, attr_id, str(value)))

def insert_multi_attributes(artist_id, prefix, values):
    for val in values:
        attr_name = f"{prefix}::{val.strip()}"
        insert_attribute_value(artist_id, attr_name, 1)

def get_or_create_style_period(name, style_type="unknown", description=""):
  cur.execute("SELECT id FROM style_periods WHERE name = ?", (name,))
  row = cur.fetchone()
  if row:
    return row[0]
  cur.execute("INSERT INTO style_periods (name, type, description) VALUES (?, ?, ?)",
        (name, style_type, description))
  return cur.lastrowid

def insert_artist_style(artist_id, style_name, role):
  style_id = get_or_create_style_period(style_name)
  cur.execute("""
    INSERT OR IGNORE INTO artist_styles (artist_id, style_period_id, role)
    VALUES (?, ?, ?)
  """, (artist_id, style_id, role))
  
def get_artist_id_by_name(name):
  cur.execute("SELECT id FROM artists WHERE canonical_name = ?", (name,))
  row = cur.fetchone()
  return row[0] if row else None

def insert_artist_influence(artist_id, influencer_name, influence_type):
  influenced_by_id = get_artist_id_by_name(influencer_name)
  if not influenced_by_id:
    # Insert placeholder if artist does not exist
    cur.execute("INSERT OR IGNORE INTO artists (canonical_name) VALUES (?)", (influencer_name,))
    influenced_by_id = get_artist_id_by_name(influencer_name)
  cur.execute("""
    INSERT OR IGNORE INTO artist_influences (artist_id, influenced_by_id, influence_type)
    VALUES (?, ?, ?)
  """, (artist_id, influenced_by_id, influence_type))
  
def insert_artist_audience_class(artist_id, audience_type_name):
  cur.execute("SELECT id FROM audience_types WHERE name = ?", (audience_type_name,))
  row = cur.fetchone()
  if row:
    audience_type_id = row[0]
    cur.execute("""
      INSERT OR IGNORE INTO artist_audience_class (artist_id, audience_type_id)
      VALUES (?, ?)
    """, (artist_id, audience_type_id))
    


def save_artist_record(record):
  canonical = record["canonical_name"]
  artist_id = get_or_create_artist(canonical)

  # INSERT structured name variants into artist_names
  for entry in record.get("names", []):
    name_type = entry.get("type")
    name_val = entry.get("value")
    if name_type and name_val:
      insert_artist_name(artist_id, name_type, name_val)

  # 1. Save audience types
  for audience_type in record.get("audience_types", []):
    insert_artist_audience_class(artist_id, audience_type)
    
  # 2. Save influences
  for influence in record.get("influences", []):
    insert_artist_influence(artist_id, influence["name"], influence["type"])
    
  # 3. Save style lineage
  for style in record.get("style_lineage", []):
    insert_artist_style(artist_id, style["style"], style["role"])
    
  
  # Flat fields
  insert_attribute_value(artist_id, "time_period", record["time_period"])
  insert_attribute_value(artist_id, "cultural_context", record["cultural_context"])
  insert_attribute_value(artist_id, "workflow_mode", record["workflow_mode"])
  
  # Arrays
  insert_multi_attributes(artist_id, "primary_medium", record["primary_medium"])
  insert_multi_attributes(artist_id, "role_identity", record["role_identity"])
  
  # Metrics
  for k, v in record["attention_metrics"].items():
    insert_attribute_value(artist_id, k, v)
    
  # Narrative context
  insert_multi_attributes(artist_id, "triggering_forces", record["narrative_context"]["triggering_forces"])
  insert_multi_attributes(artist_id, "conflict_zones", record["narrative_context"]["conflict_zones"])
  insert_attribute_value(artist_id, "legacy_mode", record["narrative_context"]["legacy_mode"])
  insert_attribute_value(artist_id, "alignment_with_power", record["narrative_context"]["alignment_with_power"])
  insert_attribute_value(artist_id, "myth_construction", record["narrative_context"]["myth_construction"])
  
  conn.commit()
  
def get_artist_data(name):
  #prompt = build_prompt(name)
  
  try:
    # 1. Create a thread
    thread = client.beta.threads.create()
    
    # 2. Add the user prompt to the thread
    client.beta.threads.messages.create(
      thread_id=thread.id,
      role="user",
      content=name
    )
    
    # 3. Run the assistant on the thread
    run = client.beta.threads.runs.create(
      thread_id=thread.id,
      assistant_id=ASSISTANT_ID
    )
    
    # 4. Wait for the run to complete (polling)
    while True:
      run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
      if run_status.status == "completed":
        break
      elif run_status.status in ["failed", "cancelled"]:
        raise Exception(f"Run failed: {run_status.status}")
      time.sleep(1)
      
    # 5. Get the latest message from the thread
    #messages = client.beta.threads.messages.list(thread_id=thread.id)
    #response_text = messages.data[0].content[0].text.value
    # On completion, extract tool output
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    message = messages.data[0]
    content = message.content[0]
    
    if hasattr(content, "tool_calls"):
      # Assistant used tool function with structured schema
      tool_call_result = content.tool_calls[0].function.arguments
      structured_data = json.loads(tool_call_result)
    else:
      # Assistant responded with plain JSON text (not using schema)
      response_text = content.text.value
      structured_data = json.loads(response_text)
      
    return structured_data
  
  except Exception as e:
    print(f"Error for {name}: {e}")
    return None

# Main loop
for name in ARTIST_NAMES:
    print(f"Processing {name}...")
    
    # Check if artist already exists
    if get_artist_id_by_name(name):
        print(f"Skipping {name}, already in database.")
        continue
    
    data = get_artist_data(name)
    if data:
        save_artist_record(data)
    time.sleep(1)  # polite pause between calls

conn.close()
