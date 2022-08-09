#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from operator import itemgetter
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

from models import *
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  venue_data = {}
  today = datetime.today()
  venue_all = Venue.query.all()
  for venue in venue_all:
    upcoming_shows = db.session.query(Show).join(Venue)\
                  .filter(Show.venue_id == venue.id)\
                  .filter(Show.start_time > today).all()
    id = venue.id
    name = venue.name
    city = venue.city
    state = venue.state
    location = (city, state)
    if location not in venue_data:
      venue_data[location] = {
        'city': city,
        'state': state,
        'venues': []
      }
    venue_data[location]['venues'].append({
      'id': id,
      'name': name,
      'num_upcoming_shows': len(upcoming_shows)
    })
    data = [venue_data[k] for k in venue_data.keys()]
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  query_string = request.form.get("search_term", "").strip()
  venue_matches = db.session.query(Venue).filter(Venue.name.ilike(f'%{query_string}%')).all()
  response_data = []
  
  for match in venue_matches:
    show_instance = {
      "id": match.id,
      "name": match.name,
      "num_upcoming_shows": len(match.shows)
    }
    response_data.append(show_instance)
    
  response = {
    "count": len(response_data),
    "data": response_data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  
  if not venue:
    flash(f"Requested venue is not found")
    return redirect(url_for('index'))
  else:
    genres = []
    for item in venue.genres:
      genres.append(item)

    now = datetime.now()
    past_shows = []
    upcoming_shows = []
    past_shows_count = 0
    upcoming_shows_count = 0

    for show in venue.shows:
      artist = Artist.query.get(show.artist_id)
      if show.start_time > now:
        upcoming_shows_count += 1
        upcoming_shows.append({
          "artist_id": show.artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": format_datetime(str(show.start_time))
        })
      elif show.start_time <= now:
        past_shows_count += 1
        past_shows.append({
          "artist_id": show.artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": format_datetime(str(show.start_time))
        })
    data = {
      "id": venue.id,
      "name": venue.name,
      "address": venue.address,
      "city": venue.city,
      "facebook_link": venue.facebook_link,
      "genres": venue.genres,
      "image_link": venue.image_link,
      "phone": venue.phone,
      "state": venue.state,
      "seeking_description": venue.seeking_description,
      "seeking_talent": venue.seeking_talent,
      "website": venue.website,
      "past_shows": past_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows": upcoming_shows,
      "upcoming_shows_count": len(upcoming_shows),
    }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  
  encountered_error = False
  try:
    form = VenueForm(request.form)
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    image_link = form.image_link.data
    website = form.website_link.data
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data
    venue = Venue(
      name=name,
      city=city,
      state=state,
      address=address,
      phone=phone,
      image_link=image_link,
      facebook_link=facebook_link,
      website=website,
      genres=genres,
      seeking_talent= True if seeking_talent == 'y' else False,
      seeking_description=seeking_description
    )
    db.session.add(venue)
    db.session.commit()
  except:
    db.session.rollback()
    encountered_error = True
    print(sys.exc_info())
  finally:
    db.session.close()
    if not encountered_error:
      flash('Venue ' + name + ' was successfully listed!')
      # TODO: on unsuccessful db insert, flash an error instead.
    if encountered_error:
      flash('Venue ' + name + ' could not be listed!')
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    venue.delete()
    db.session.commit()
    flash("Venue: " + Venue.query.get(venue_id).name + " was successfully deleted.")
  except:
    db.session.rollback()
    print(sys.exc_info())
    return flash('Something went wrong: Venue could not be deleted.')
  finally:
    db.session.close()
    return redirect(url_for("index"))
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  
  data = []
  for art in artists:
    data.append({
      "id": art.id,
      "name": art.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  query = request.form.get('search_term', '')
  artists_all = Artist.query.filter(Artist.name.ilike(f'%{query}%')).all()
  response = {
    "count": len(artists_all),
    "data": artists_all
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  try:
    artist = Artist.query.get(artist_id)
    today = datetime.today()
    data = {}
    past_shows = []
    upcoming_shows = []
    if not artist:
      flash(f"Artist not found")
      return redirect(url_for('index'))
    shows = Show.query.filter(Show.artist_id==artist_id).all()
    for show in shows:
      if show.start_time >= today:
        upcoming_shows.append({
          'venue_id': show.venue.id,
          'venue_name': show.venue.name,
          'venue_image_link': show.venue.image_link,
          'start_time': format_datetime(str(show.start_time))
        })
      else:
        past_shows.append({
          'venue_id': show.venue.id,
          'venue_name': show.venue.name,
          'venue_image_link': show.venue.image_link,
          'start_time': format_datetime(str(show.start_time))
        })
    data = {
      'id': artist.id,
      'name': artist.name,
      'genres': artist.genres,
      'city': artist.city,
      'state': artist.state,
      'phone': artist.phone,
      'website': artist.website,
      'facebook_link': artist.facebook_link,
      'seeking_venue': artist.seeking_venue,
      'seeking_description': artist.seeking_description,
      'image_link': artist.image_link,
      'past_shows': past_shows,
      'upcoming_shows': upcoming_shows,
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows),
    }
  except:
    print(sys.exc_info())
    flash("An error occured, Please try again.")
  finally:
    db.session.close()
  
  # data1={
  #   "id": 4,
  #   "name": "Guns N Petals",
  #   "genres": ["Rock n Roll"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "326-123-5000",
  #   "website": "https://www.gunsnpetalsband.com",
  #   "facebook_link": "https://www.facebook.com/GunsNPetals",
  #   "seeking_venue": True,
  #   "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #   "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "past_shows": [{
  #     "venue_id": 1,
  #     "venue_name": "The Musical Hop",
  #     "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #     "start_time": "2019-05-21T21:30:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data2={
  #   "id": 5,
  #   "name": "Matt Quevedo",
  #   "genres": ["Jazz"],
  #   "city": "New York",
  #   "state": "NY",
  #   "phone": "300-400-5000",
  #   "facebook_link": "https://www.facebook.com/mattquevedo923251523",
  #   "seeking_venue": False,
  #   "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "past_shows": [{
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2019-06-15T23:00:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data3={
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  #   "genres": ["Jazz", "Classical"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "432-325-5432",
  #   "seeking_venue": False,
  #   "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "past_shows": [],
  #   "upcoming_shows": [{
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-01T20:00:00.000Z"
  #   }, {
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-08T20:00:00.000Z"
  #   }, {
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-15T20:00:00.000Z"
  #   }],
  #   "past_shows_count": 0,
  #   "upcoming_shows_count": 3,
  # }
  
  # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  if not artist:
    flash(f"Artist not found")
    return redirect(url_for('index'))
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    form = ArtistForm(request.form)
    artist = Artist.query.get(artist_id)
    if not artist:
      flash("Artist not found")
      return redirect(url_for('index'))

    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = form.genres.data
    artist.facebook_link = form.facebook_link.data
    artist.website = form.website.data
    artist.image_link = form.image_link.data
    db.session.add(artist)
    db.session.commit()
    flash(f"{artist.name} profile has been updated!")
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash("Some error occured. Please retry")
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  # TODO: populate form with values from venue with ID <venue_id>
  
  venue = Venue.query.get(venue_id)
  if not venue:
    flash("Venue not found")
    return redirect(url_for('index'))
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)
  if not venue:
    flash(f"Venue doesn't exist")
    return redirect(url_for('index'))

  try:
    form = VenueForm()
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone =  form.phone.data
    venue.genres = form.genres.data
    venue.website =  form.website.data
    venue.address =  form.address.data
    venue.image_link =form.image_link.data
    venue.facebook_link =form.facebook_link.data
    venue.seeking_talent = True if form.seeking_talent.data == 'y' else False
    venue.seeking_description = form.seeking_description.data
    db.session.add(venue)
    db.session.commit()
    flash(f"{venue.name} has been updated")
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash("Some error occured, please try again")
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error_occured = False
  try:
    form = ArtistForm()
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    website = form.website_link.data
    image_link = form.image_link.data
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data

    artist = Artist(
      name=name,
      city=city,
      state=state,
      phone=phone,
      genres=genres,
      facebook_link=facebook_link,
      image_link=image_link,
      website=website,
      seeking_venue=True if seeking_venue == 'y' else False,
      seeking_description=seeking_description
    )
    print('artistartistartistartistartist: ', artist)
    db.session.add(artist)
    db.session.commit()
    flash(f"{name} is successfully listed!")
  except:
    error_occured = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if not error_occured:
    flash(f"{name} is successfully listed")
    return redirect(url_for('index'))
  else:
    flash('Some error occurred. Please try again.')
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  try:
    shows = Show.query.all()
    for show in shows:
      venue = Venue.query.get(show.venue_id)
      artist = Artist.query.get(show.artist_id)
      data.append({
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": format_datetime(str(show.start_time))
      })

  except:
    db.session.rollback()
    print(sys.exc_info())
    flash("Something went wrong. Please try again.")

  finally:
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error_occured = False
  try:
    form = ShowForm()
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data
    
    artist = Artist.query.get(artist_id)
    if artist is None:
      error_occured = True
      return flash("Artist not found")
    venue = Venue.query.get(venue_id)
    if venue is None:
      error_occured = True
      return flash("Venue not found")
    show = Show(
      artist_id=artist.id,
      venue_id=venue.id,
      start_time=start_time,
    )
    db.session.add(show)
    db.session.commit()
  except:
    error_occured = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
    if error_occured:
      flash('An error occurred. Show could not be listed.')
    else:
      flash('Show was successfully listed!')
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''