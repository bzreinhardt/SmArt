#!/usr/bin/python
from flask import Flask, url_for, json,  request 
from scipy.spatial import distance
import os
import boto3
import random
import string
from flask_sqlalchemy import SQLAlchemy

#DB jsonat 
# [{name:foo, gps:(1,1), }, {} ...]

# These should be in a json config
METADATA = ['artistName', 
            'pieceName', 
            'instagram', 
            'location',
            'instagram']
LOCATION = ['lat', 'long']
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = PROJECT_ROOT + '/art_db.json'
BUCKET_NAME='akiajqulpiyv2ovwdt4a-dump'

app = Flask(__name__)
if os.environ.get('DATABASE_URL'):
  app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
else:
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class Art(db.Model):
    key = db.Column(db.String(120), primary_key=True)
    artist_name = db.Column(db.String(80))
    piece_name = db.Column(db.String(120))
    latitutde = db.Column(db.Float)
    longitude = db.Column(db.Float)
    bucket = db.Column(db.String(80))
    instagram = db.Column(db.String(80))
    #notes = db.Column(db.String(120))


    def __init__(self, key, artist_name='', piece_name='', latitutde=0.0, longitude=0.0, bucket = '',
                 instagram = '', notes='', json_dict=None):
        self.key = key
        self.artist_name = artist_name
        self.piece_name = piece_name
        self.latitutde = latitutde
        self.longitude = longitude
        self.bucket = bucket
        self.instagragm = instagram
        #self.notes = notes

        if json_dict is not None:
          if json_dict.has_key('artistName'):
            self.artist_name = json_dict['artistName']
          if json_dict.has_key('pieceName'):
            self.piece_name = json_dict['pieceName']
          if json_dict.has_key('location'):
            self.latitutde = json_dict['location']['lat']
            self.longitude = json_dict['location']['long']
          if json_dict.has_key('instagram'):
            self.instagram = json_dict['instagram']
          #if json_dict.has_key('notes'):
          # self.notes = json_dict['notes']


    def __repr__(self):
        return '<Artist Name: %r>' % self.artist_name


def save_to_s3(key, data):
  s3 = boto3.resource('s3')
  s3.Bucket(BUCKET_NAME).put_object(Key=key, Body=data)
 

def find_closest_art(db, coords):
  # Returns index of closest art piece
  # This is the stupidest version. Actually looping
  dists = []
  for art in db:
    dists.append(distance.cdist([(art['location']['lat'],art['location']['long'])], coords))
  return dists.index(min(dists))


@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
  
  rand = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
  if not request.form.has_key('artistName'):
    request.form['artistName'] = 'noname'
  key = request.form['artistName'] + rand
 
  
  art = Art(key, bucket=BUCKET_NAME, json_dict=request.form)
  db.session.add(art)
  db.session.commit()
  data = request.files['image'].stream.read()
  print "DATA SIZE: %s"%len(data)
  save_to_s3(key, data)
  print "SAVED TO KEY: %s"%key
  return 'success'

@app.route('/lookup', methods=['GET', 'POST'])
def lookup_gps():
  coords = [(request.json['location']['lat'], request.json['location']['long'])]
  if len(app.DB) == 0:
    app.DB = load_db(DB_PATH)
  index = find_closest_art(app.DB, coords)
  return json.dumps({'name':app.DB[index]['name'], 'instagram':app.DB[index]['instagram']})


@app.route('/')
def api_root():
  return Art.query.all()


if __name__ == '__main__':
  
  app.debug = True
  app.run()
