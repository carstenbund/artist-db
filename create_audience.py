import sqlite3

# Reconnect after state reset
conn = sqlite3.connect("artist_scorecards.db")
cur = conn.cursor()

# Extend schema: add audience_types and artist_audience_class linking table
cur.executescript("""
CREATE TABLE IF NOT EXISTS audience_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS artist_audience_class (
    artist_id INTEGER NOT NULL,
    audience_type_id INTEGER NOT NULL,
    PRIMARY KEY (artist_id, audience_type_id),
    FOREIGN KEY (artist_id) REFERENCES artists(id),
    FOREIGN KEY (audience_type_id) REFERENCES audience_types(id)
);
""")

# Prepopulate audience_types with a typology
audience_typology = [
    ("Institutional", "Museums, state commissions, academia"),
    ("Public Spectacle", "Mass media, public controversy, global fame"),
    ("Cult/Niche", "Small devoted followings, rediscovery narratives"),
    ("Peer Circle", "Other artists, critics, intellectual networks"),
    ("Internalized", "No audience intended, inwardly driven creation")
]

cur.executemany("""
INSERT OR IGNORE INTO audience_types (name, description) VALUES (?, ?)
""", audience_typology)

conn.commit()
conn.close()

"Schema extended: audience_types and artist_audience_class tables created, initial categories seeded."

