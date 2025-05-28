# artist-db

A small SQLite database of artists with influences and styles.

## Database setup

Run the table creation scripts to generate `artist_scorecards.db`:

```bash
python create_tables.py
python create_styles.py
python create_audience.py
```

## Browsing the data

Install dependencies and start the Flask application:

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000/` to navigate styles and artists. Pages include
links to influenced artists and their influencers, as well as hierarchical
style navigation.
