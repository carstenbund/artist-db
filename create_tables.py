import sqlite3

# Connect to SQLite (or create new DB)
conn = sqlite3.connect("artist_scorecards.db")
cur = conn.cursor()

# Drop existing tables if they exist (for clean re-run during testing)
cur.execute("DROP TABLE IF EXISTS artist_attributes")
cur.execute("DROP TABLE IF EXISTS artist_names")
cur.execute("DROP TABLE IF EXISTS attributes")
cur.execute("DROP TABLE IF EXISTS artists")

# Create master artist table with canonical name
cur.execute("""
CREATE TABLE artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT UNIQUE NOT NULL
)
""")

# Create artist_names for structured name handling
cur.execute("""
CREATE TABLE artist_names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id INTEGER NOT NULL,
    name_type TEXT NOT NULL,   -- e.g., 'birth_name', 'known_as', 'mononym'
    name TEXT NOT NULL,
    FOREIGN KEY (artist_id) REFERENCES artists(id)
)
""")

# Attribute registry
cur.execute("""
CREATE TABLE attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)
""")

# Key-value store for artist attributes
cur.execute("""
CREATE TABLE artist_attributes (
    artist_id INTEGER NOT NULL,
    attribute_id INTEGER NOT NULL,
    value TEXT,
    PRIMARY KEY (artist_id, attribute_id),
    FOREIGN KEY (artist_id) REFERENCES artists(id),
    FOREIGN KEY (attribute_id) REFERENCES attributes(id)
)
""")

conn.commit()
conn.close()

"SQLite schema created successfully at /mnt/data/artist_scorecards.db"

