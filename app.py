from flask import Flask, render_template, request
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker, declarative_base, scoped_session

DATABASE_URL = 'sqlite:///artist_scorecards.db'

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

class Artist(Base):
    __tablename__ = 'artists'
    id = Column(Integer, primary_key=True)
    canonical_name = Column(String, unique=True)

    styles = relationship('StylePeriod', secondary='artist_styles', back_populates='artists')
    influences = relationship('ArtistInfluence', foreign_keys='ArtistInfluence.artist_id', back_populates='artist')
    followers = relationship('ArtistInfluence', foreign_keys='ArtistInfluence.influenced_by_id', back_populates='influencer')

class StylePeriod(Base):
    __tablename__ = 'style_periods'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    type = Column(String)
    description = Column(String)
    parent_id = Column(Integer, ForeignKey('style_periods.id'))

    parent = relationship('StylePeriod', remote_side=[id], backref='children')
    artists = relationship('Artist', secondary='artist_styles', back_populates='styles')

class ArtistStyle(Base):
    __tablename__ = 'artist_styles'
    artist_id = Column(Integer, ForeignKey('artists.id'), primary_key=True)
    style_period_id = Column(Integer, ForeignKey('style_periods.id'), primary_key=True)
    role = Column(String)

class ArtistInfluence(Base):
    __tablename__ = 'artist_influences'
    artist_id = Column(Integer, ForeignKey('artists.id'), primary_key=True)
    influenced_by_id = Column(Integer, ForeignKey('artists.id'), primary_key=True)
    influence_type = Column(String)

    artist = relationship('Artist', foreign_keys=[artist_id], back_populates='influences')
    influencer = relationship('Artist', foreign_keys=[influenced_by_id], back_populates='followers')

app = Flask(__name__)

@app.teardown_appcontext
def remove_session(exception=None):
    SessionLocal.remove()

@app.route('/')
def index():
    session = SessionLocal()
    styles = session.query(StylePeriod).filter(StylePeriod.parent_id == None).order_by(StylePeriod.name).all()
    return render_template('index.html', styles=styles)

@app.route('/style/<int:style_id>')
def style_detail(style_id):
    session = SessionLocal()
    style = session.query(StylePeriod).get(style_id)
    if not style:
        return 'Style not found', 404
    page = int(request.args.get('page', 1))
    per_page = 20
    artists_query = session.query(Artist).join(ArtistStyle).filter(ArtistStyle.style_period_id == style_id).order_by(Artist.canonical_name)
    total = artists_query.count()
    artists = artists_query.offset((page-1)*per_page).limit(per_page).all()
    return render_template('style.html', style=style, children=style.children, artists=artists, page=page, per_page=per_page, total=total)

@app.route('/artist/<int:artist_id>')
def artist_detail(artist_id):
    session = SessionLocal()
    artist = session.query(Artist).get(artist_id)
    if not artist:
        return 'Artist not found', 404
    influences = [inf.influencer for inf in artist.influences]
    followers = [inf.artist for inf in artist.followers]
    return render_template('artist.html', artist=artist, influences=influences, followers=followers)

if __name__ == '__main__':
    app.run(debug=True)
