#!/usr/bin/python
from flask import Flask, url_for, json,  request 
from scipy.spatial import distance

#DB jsonat 
# [{name:foo, gps:(1,1), }, {} ...]
DB_PATH='./art_db.json'
METADATA = ['name', 'artist', 'instagram', 'notes']

DB = []

app = Flask(__name__)

def add_to_db(info, db):
  db.append(info)
  with open(DB_PATH, 'w') as f:
    f.write(json.dumps(db))   

def find_closest_art(db, coords):
  # Returns index of closest art piece
  # This is the stupidest version. Actually looping
  dists = []
  for art in db:
    dists.append(distance.cdist([(art['lat'],art['lon'])], coords))
  return dists.index(min(dists))


def load_db(db_path):
  with open(DB_PATH, 'r') as f:
    db = json.loads(f.read())
  return db

@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
  info = request.json
  for datum in METADATA:
    if not info.has_key(datum):
      info[datum] = 'none'
  add_to_db(info, DB)
  return 'success'

@app.route('/lookup', methods=['GET', 'POST'])
def lookup_gps():
  coords = [(request.json['lat'], request.json['lon'])]
  index = find_closest_art(DB, coords)
  return json.dumps({'name':DB[index]['name'], 'instagram':DB[index]['instagram']})


@app.route('/')
def api_root():
  return 'Welcome'


if __name__ == '__main__':
  DB = load_db(DB_PATH)
  app.debug = True
  app.run()
