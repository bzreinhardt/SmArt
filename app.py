#!/usr/bin/python
from flask import Flask, url_for, json,  request 
from scipy.spatial import distance
import os
import boto3
import random
import string


#DB jsonat 
# [{name:foo, gps:(1,1), }, {} ...]

METADATA = ['artistName', 'name', 'artist', 'instagram', 'notes', 'location']
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = PROJECT_ROOT + '/art_db.json'
BUCKET_NAME='akiajqulpiyv2ovwdt4a-dump'

def save_to_s3(key, data):
  s3 = boto3.resource('s3')
  s3.Bucket(BUCKET_NAME).put_object(Key=key, Body=data)

def load_db(db_path):
  with open(DB_PATH, 'r') as f:
    db = json.loads(f.read())
  return db

app = Flask(__name__)
app.DB = load_db(DB_PATH)
print "DB SIZE IS: %d"%(len(app.DB))



def add_to_db(info, db):
  db.append(info)
  with open(DB_PATH, 'w') as f:
    f.write(json.dumps(db))   

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
