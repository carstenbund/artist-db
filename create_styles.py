import sqlite3

# Connect to the database
conn = sqlite3.connect("artist_scorecards.db")
cur = conn.cursor()

# Schema extension: styles, influence relationships, audience types already created
cur.executescript("""
-- Style / Period / Movement Table
CREATE TABLE IF NOT EXISTS style_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    type TEXT, -- e.g., 'movement', 'period', 'direction'
    description TEXT
);

-- Artist-Style Relationship Table
CREATE TABLE IF NOT EXISTS artist_styles (
    artist_id INTEGER NOT NULL,
    style_period_id INTEGER NOT NULL,
    role TEXT, -- e.g., 'follower', 'founder', 'influenced_by'
    PRIMARY KEY (artist_id, style_period_id),
    FOREIGN KEY (artist_id) REFERENCES artists(id),
    FOREIGN KEY (style_period_id) REFERENCES style_periods(id)
);

-- Artist-Influence Self-Reference Table
CREATE TABLE IF NOT EXISTS artist_influences (
    artist_id INTEGER NOT NULL,
    influenced_by_id INTEGER NOT NULL,
    influence_type TEXT,
    PRIMARY KEY (artist_id, influenced_by_id),
    FOREIGN KEY (artist_id) REFERENCES artists(id),
    FOREIGN KEY (influenced_by_id) REFERENCES artists(id)
);
""")

conn.commit()
conn.close()

"Schema extended with style_periods, artist_styles, and artist_influences tables."

