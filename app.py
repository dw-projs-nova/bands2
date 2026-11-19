from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from dotenv import load_dotenv
from model import AlbumCredits, Memberships, db, Bands, Members, Albums, admin
from flask_admin.contrib.sqla import ModelView
import os

# Create our Flask app object
app = Flask(__name__)

# Configure the flask app instance
CONFIG_TYPE = os.getenv('CONFIG_TYPE', default='config.DevelopmentConfig')
app.config.from_object(CONFIG_TYPE)

# Create an instance of SQLAlchemy as our db object
db.init_app(app)

admin.init_app(app)
admin.add_view(ModelView(Bands, db.session, category="Bands"))
admin.add_view(ModelView(Members, db.session, category="Members"))
admin.add_view(ModelView(Albums, db.session, category="Albums"))
admin.add_view(ModelView(Memberships, db.session, category="Members"))
admin.add_view(ModelView(AlbumCredits, db.session, category="Albums"))


# ==========================
# ROUTES
# ==========================

# Home page view


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bands/view')
def view_by_band():
    q = request.args.get('q', '').strip()

    query = Bands.query
    if q:
        like_q = f"%{q}%"
        query = (
            query.outerjoin(Memberships, Bands.BandID == Memberships.BandID)
            .outerjoin(Members, Memberships.MemberID == Members.MemberID)
            .outerjoin(Albums, Bands.BandID == Albums.BandID)
            .filter(
                or_(
                    Bands.BandName.ilike(like_q),
                    Bands.HomeLocation.ilike(like_q),
                    Members.MemberName.ilike(like_q),
                    Memberships.Role.ilike(like_q),
                    Albums.AlbumTitle.ilike(like_q),
                )
            )
            .distinct()
        )

    bands = query.order_by(Bands.BandName).all()
    return render_template('display_by_band.html', bands=bands, q=q)


@app.route('/bands/view/<int:id>')
def view_band(id):
    band = Bands.query.get_or_404(id)
    memberships = Memberships.query.filter_by(BandID=id).all()
    return render_template('view_band.html', band=band, memberships=memberships)


@app.route('/bands/add', methods=['GET', 'POST'])
def add_band():
    if request.method == 'POST':
        new_band = Bands(
            BandName=request.form['bandname'],
            FormedYear=request.form['formedyear'],
            HomeLocation=request.form['homelocation']
        )
        db.session.add(new_band)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_band.html')
@app.route('/bands/edit/<int:id>', methods=['GET', 'POST'])
def edit_band(id):
    band = Bands.query.get_or_404(id)
    if request.method == 'POST':
        try:
            band.BandName = request.form['bandname']
            band.FormedYear = request.form['formedyear']
            band.HomeLocation = request.form['homelocation']
            db.session.commit()
            # flash('Band updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error updating band: {e}")
        return redirect(url_for('view_by_band'))
    return render_template('edit_band.html', band=band)
@app.route('/bands/delete/<int:id>', methods=['POST'])
def delete_band(id):
    band = Bands.query.get_or_404(id)

    try:
        db.session.delete(band)
        db.session.commit()
        # flash('Band deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting band: {e}")
    return redirect(url_for('view_by_band'))

@app.route('/members/view')
def view_members():
    members = Members.query.all()
    memberships = Memberships.query.all()
    return render_template('display_by_member.html', members=members, memberships=memberships)
@app.route('/members/view/<int:id>')
def view_member(id):
    member = Members.query.get_or_404(id)
    memberships = Memberships.query.filter_by(MemberID=id).all()
    return render_template('view_member.html', member=member, memberships=memberships)
@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    bands = Bands.query.all()  # Students see querying with relationships
    if request.method == 'POST':
        new_member = Members(
            MemberName=request.form['membername'],
            MainPosition=request.form['mainposition'],
            BandID=request.form['bandid']
        )
        db.session.add(new_member)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_member.html', bands=bands)

@app.route('/memberships/add', methods=['GET', 'POST'])
def add_membership():
    bands = Bands.query.all()
    members = Members.query.all()
    if request.method == 'POST':
        try:
            new_membership = Memberships(
                BandID=request.form['bandid'],
                MemberID=request.form['memberid'],
                Role=request.form['role'],
                StartYear=request.form['startyear'],
                EndYear=request.form['endyear'] if request.form['endyear'] else None
            )
            db.session.add(new_membership)
            db.session.commit()
            # flash('Membership added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error adding membership: {e}")
    return render_template('add_membership.html', bands=bands, members=members)

@app.route('/memberships/edit/<int:id>', methods=['GET', 'POST'])
def edit_membership(id):
    membership = Memberships.query.get_or_404(id)
    bands = Bands.query.all()
    members = Members.query.all()
    if request.method == 'POST':
        membership.MembershipID = request.form['membershipid']
        membership.BandID = request.form['bandid']
        membership.MemberID = request.form['memberid']
        membership.Role = request.form['role']
        membership.StartYear = request.form['startyear'] if request.form['startyear'] else None
        membership.EndYear = request.form['endyear'] if request.form['endyear'] else None
        db.session.commit()
        # flash('Membership updated successfully!', 'success')
        return redirect(url_for('view_by_band'))
    return render_template('edit_membership.html', membership=membership, bands=bands, members=members)
@app.route('/memberships/delete/<int:id>', methods=['POST'])
def delete_membership(id):
    membership = Memberships.query.get_or_404(id)
    db.session.delete(membership)
    db.session.commit()
    # flash('Membership deleted successfully!', 'success')
    return redirect(url_for('view_by_band'))

@app.route('/albums/<int:id>')
def view_album(id):
    album = Albums.query.get_or_404(id)
    collaborators = [
        credit for credit in album.album_credits if credit.BandID != album.BandID
    ]
    return render_template(
        'view_album.html',
        album=album,
        collaborators=collaborators,
    )
@app.route('/albums/add', methods=['GET', 'POST'])
def add_album():
    bands = Bands.query.all()
    if request.method == 'POST':
        new_album = Albums(
            AlbumTitle=request.form['albumtitle'],
            ReleaseYear=request.form['releaseyear'],
            BandID=request.form['bandid']
        )
        db.session.add(new_album)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_album.html', bands=bands)


# Create DB and tables if they don't exist
with app.app_context():
    db.create_all()

# Run the app if this file is launched via Python (instead of flask run --debug)
if __name__ == '__main__':
    app.run(debug=True)
