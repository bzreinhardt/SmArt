#!/usr/bin/python
from flask import Flask, url_for, json,  request 
from scipy.spatial import distance
import os
import boto3
import random
import string
from flask.ext.sqlalchemy import SQLAlchemy

#DB jsonat 
# [{name:foo, gps:(1,1), }, {} ...]

METADATA = ['artistName', 'pieceName', 'instagram', 'notes', 'location']
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = PROJECT_ROOT + '/art_db.json'
BUCKET_NAME='akiajqulpiyv2ovwdt4a-dump'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
print "DB SIZE IS: %d"%(len(app.DB))

class Art(db.Model):
    key = db.Column(db.String(120), primary_key=True)
    artist_name = db.Column(db.String(80))
    piece_name = db.Column(db.String(120))
    latitutde = db.Column(db.Double)
    longitude = db.Column(db.Double)
    bucket = db.Column(db.String(80))
    instagram = db.Column(db.String(80))


    def __init__(self, key, artist_name='', piece_name='', latitutde='', longitude='', bucket = '',
                 instagram = ''):
        self.key = key
        self.artist_name = artist_name
        self.piece_name = piece_name
        self.latitutde = latitutde
        self.longitude = longitude

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
  info = {}
  #import pdb
  #pdb.set_trace()
  for key in request.form.keys():
    print "KEY IS: " + key
    print "VALUE IS: " + request.form[key]
  for datum in METADATA:
    if request.form.has_key(datum):
      info[datum] = request.form[datum]
  rand = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
  key = info['artistName'] + rand
  info['key'] = key
  info['aws_bucket'] = BUCKET_NAME
  add_to_db(info, app.DB)
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
  return 'Welcome'


if __name__ == '__main__':
  
  app.debug = True
  app.run()
