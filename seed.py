import os
import sqlite3
import traceback
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "bands2.db")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
admin = Admin(app)


class Bands(db.Model):
    BandID = db.Column(db.Integer, primary_key=True)
    BandName = db.Column(db.String(80), nullable=False)
    FormedYear = db.Column(db.Integer)
    HomeLocation = db.Column(db.String(80))
    members = db.relationship("Memberships", backref="band", lazy=True)
    albums = db.relationship("Albums", backref="band", lazy=True)
    album_credits = db.relationship("AlbumCredits", backref="band", lazy=True)


class Members(db.Model):
    MemberID = db.Column(db.Integer, primary_key=True)
    MemberName = db.Column(db.String(80), nullable=False)
    MainPosition = db.Column(db.String(80))
    memberships = db.relationship("Memberships", backref="member", lazy=True)


class Memberships(db.Model):
    MembershipID = db.Column(db.Integer, primary_key=True)
    BandID = db.Column(db.Integer, db.ForeignKey("bands.BandID"), nullable=False)
    MemberID = db.Column(db.Integer, db.ForeignKey("members.MemberID"), nullable=False)
    Role = db.Column(db.String(80))
    StartYear = db.Column(db.Integer)
    EndYear = db.Column(db.Integer)


class Albums(db.Model):
    AlbumID = db.Column(db.Integer, primary_key=True)
    BandID = db.Column(db.Integer, db.ForeignKey("bands.BandID"), nullable=False)
    AlbumTitle = db.Column(db.String(80), nullable=False)
    ReleaseYear = db.Column(db.Integer)
    album_credits = db.relationship("AlbumCredits", backref="album", lazy=True)


class AlbumCredits(db.Model):
    AlbumCreditID = db.Column(db.Integer, primary_key=True)
    BandID = db.Column(db.Integer, db.ForeignKey("bands.BandID"), nullable=False)
    AlbumID = db.Column(db.Integer, db.ForeignKey("albums.AlbumID"), nullable=False)
    CreditType = db.Column(db.String(40), nullable=False, default="Collaborator")


def get_or_create_band(name, formed_year, home_location):
    band = Bands.query.filter_by(BandName=name).first()
    if not band:
        band = Bands(BandName=name, FormedYear=formed_year, HomeLocation=home_location)
        db.session.add(band)
        db.session.flush()
    return band


def get_or_create_member(name, main_position):
    member = Members.query.filter_by(MemberName=name).first()
    if not member:
        member = Members(MemberName=name, MainPosition=main_position)
        db.session.add(member)
        db.session.flush()
    return member


def get_or_create_membership(band, member, role, start_year, end_year=None):
    membership = Memberships.query.filter_by(
        BandID=band.BandID,
        MemberID=member.MemberID,
        Role=role,
        StartYear=start_year,
    ).first()
    if not membership:
        membership = Memberships(
            BandID=band.BandID,
            MemberID=member.MemberID,
            Role=role,
            StartYear=start_year,
            EndYear=end_year,
        )
        db.session.add(membership)
        db.session.flush()
    return membership


def get_or_create_album(primary_band, title, release_year):
    album = Albums.query.filter_by(AlbumTitle=title, ReleaseYear=release_year).first()
    if not album:
        album = Albums(
            BandID=primary_band.BandID,
            AlbumTitle=title,
            ReleaseYear=release_year,
        )
        db.session.add(album)
        db.session.flush()
    return album


def get_or_create_album_credit(band, album, credit_type=None):
    existing = AlbumCredits.query.filter_by(
        BandID=band.BandID,
        AlbumID=album.AlbumID,
    ).first()
    if not existing:
        kwargs = {"BandID": band.BandID, "AlbumID": album.AlbumID}
        if credit_type is not None:
            kwargs["CreditType"] = credit_type
        existing = AlbumCredits(**kwargs)
        db.session.add(existing)
        db.session.flush()
    return existing


def verify_database(db_path):
    print("\n--- VERIFICATION ---")
    print("Target DB path :", db_path)
    print("File exists    :", os.path.exists(db_path))
    if os.path.exists(db_path):
        print("File size (B)  :", os.path.getsize(db_path))

    print("ORM counts     :", {
        "Bands": Bands.query.count(),
        "Members": Members.query.count(),
        "Memberships": Memberships.query.count(),
        "Albums": Albums.query.count(),
        "AlbumCredits": AlbumCredits.query.count(),
    })

    # Read directly via raw sqlite3 on a fresh connection to confirm disk persistence
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = [
        r[0]
        for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    ]
    print("SQLite tables  :", tables)
    sample_bands = cur.execute(
        "SELECT BandID, BandName, FormedYear FROM bands ORDER BY BandID"
    ).fetchall()
    print("Sample bands   :", sample_bands)
    conn.close()
    print("--------------------\n")


def seed():
    print("Starting seeder...")
    print("Existed before :", os.path.exists(DB_PATH))

    db.create_all()

    beatles = get_or_create_band("The Beatles", 1960, "Liverpool, England")
    queen = get_or_create_band("Queen", 1971, "London, England")
    fleetwood_mac = get_or_create_band("Fleetwood Mac", 1967, "London, England")
    velvet_underground = get_or_create_band("The Velvet Underground", 1964, "New York City, NY")
    nico_solo = get_or_create_band("Nico", 1967, "New York City, NY")
    talking_heads = get_or_create_band("Talking Heads", 1975, "New York City, NY")
    tom_tom_club = get_or_create_band("Tom Tom Club", 1981, "New York City, NY")

    lennon = get_or_create_member("John Lennon", "Rhythm Guitar & Vocals")
    mccartney = get_or_create_member("Paul McCartney", "Bass & Vocals")
    harrison = get_or_create_member("George Harrison", "Lead Guitar & Vocals")
    starr = get_or_create_member("Ringo Starr", "Drums & Vocals")
    mercury = get_or_create_member("Freddie Mercury", "Lead Vocals & Piano")
    may = get_or_create_member("Brian May", "Lead Guitar & Vocals")
    taylor = get_or_create_member("Roger Taylor", "Drums & Vocals")
    deacon = get_or_create_member("John Deacon", "Bass Guitar")
    fleetwood = get_or_create_member("Mick Fleetwood", "Drums & Percussion")
    mcview = get_or_create_member("John McVie", "Bass Guitar")
    christine_mcview = get_or_create_member("Christine McVie", "Keyboards & Vocals")
    buckingham = get_or_create_member("Lindsey Buckingham", "Lead Guitar & Vocals")
    nicks = get_or_create_member("Stevie Nicks", "Vocals")
    reed = get_or_create_member("Lou Reed", "Vocals & Guitar")
    cale = get_or_create_member("John Cale", "Viola, Bass & Keyboards")
    morrison = get_or_create_member("Sterling Morrison", "Guitar & Bass")
    tucker = get_or_create_member("Maureen Tucker", "Drums & Percussion")
    nico = get_or_create_member("Nico", "Vocals & Harmonium")
    byrne = get_or_create_member("David Byrne", "Vocals & Guitar")
    weymouth = get_or_create_member("Tina Weymouth", "Bass Guitar")
    frantz = get_or_create_member("Chris Frantz", "Drums & Percussion")
    jerry_harrison = get_or_create_member("Jerry Harrison", "Keyboards & Guitar")

    get_or_create_membership(beatles, lennon, "Rhythm Guitar & Vocals", 1960, 1970)
    get_or_create_membership(beatles, mccartney, "Bass & Vocals", 1960, 1970)
    get_or_create_membership(beatles, harrison, "Lead Guitar & Vocals", 1960, 1970)
    get_or_create_membership(beatles, starr, "Drums & Vocals", 1962, 1970)

    get_or_create_membership(queen, mercury, "Lead Vocals & Piano", 1971, 1991)
    get_or_create_membership(queen, may, "Lead Guitar & Vocals", 1971, None)
    get_or_create_membership(queen, taylor, "Drums & Vocals", 1971, None)
    get_or_create_membership(queen, deacon, "Bass Guitar", 1971, 1997)

    get_or_create_membership(fleetwood_mac, fleetwood, "Drums & Percussion", 1967, None)
    get_or_create_membership(fleetwood_mac, mcview, "Bass Guitar", 1967, None)
    get_or_create_membership(fleetwood_mac, christine_mcview, "Keyboards & Vocals", 1970, 2022)
    get_or_create_membership(fleetwood_mac, buckingham, "Lead Guitar & Vocals", 1974, 2018)
    get_or_create_membership(fleetwood_mac, nicks, "Vocals", 1974, None)

    get_or_create_membership(velvet_underground, reed, "Vocals & Guitar", 1964, 1970)
    get_or_create_membership(velvet_underground, cale, "Viola, Bass & Keyboards", 1964, 1968)
    get_or_create_membership(velvet_underground, morrison, "Guitar & Bass", 1965, 1971)
    get_or_create_membership(velvet_underground, tucker, "Drums & Percussion", 1965, 1971)
    get_or_create_membership(velvet_underground, nico, "Vocals", 1966, 1967)
    get_or_create_membership(nico_solo, nico, "Lead Vocals & Harmonium", 1967, 1988)

    get_or_create_membership(talking_heads, byrne, "Vocals & Guitar", 1975, 1991)
    get_or_create_membership(talking_heads, weymouth, "Bass Guitar", 1975, 1991)
    get_or_create_membership(talking_heads, frantz, "Drums & Percussion", 1975, 1991)
    get_or_create_membership(talking_heads, jerry_harrison, "Keyboards & Guitar", 1977, 1991)

    get_or_create_membership(tom_tom_club, weymouth, "Bass & Vocals", 1981, None)
    get_or_create_membership(tom_tom_club, frantz, "Drums & Vocals", 1981, None)

    sgt_pepper = get_or_create_album(beatles, "Sgt. Pepper's Lonely Hearts Club Band", 1967)
    night_at_opera = get_or_create_album(queen, "A Night at the Opera", 1975)
    rumours = get_or_create_album(fleetwood_mac, "Rumours", 1977)
    vu_and_nico = get_or_create_album(velvet_underground, "The Velvet Underground & Nico", 1967)
    remain_in_light = get_or_create_album(talking_heads, "Remain in Light", 1980)
    tom_tom_debut = get_or_create_album(tom_tom_club, "Tom Tom Club", 1981)

    get_or_create_album_credit(nico_solo, vu_and_nico)
    get_or_create_album_credit(tom_tom_club, remain_in_light)
    get_or_create_album_credit(talking_heads, tom_tom_debut)

    db.session.commit()
    verify_database(DB_PATH)


if __name__ == "__main__":
    try:
        with app.app_context():
            seed()
    except Exception:
        print("SEEDER FAILED WITH ERROR:")
        traceback.print_exc()