#!/usr/bin/python
from flask import Flask, url_for, json,  request 
from scipy.spatial import distance
import os

#DB jsonat 
# [{name:foo, gps:(1,1), }, {} ...]

METADATA = ['name', 'artist', 'instagram', 'notes']
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = PROJECT_ROOT + '/art_db.json'

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
    dists.append(distance.cdist([(art['lat'],art['lon'])], coords))
  return dists.index(min(dists))


@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
  info = request.json
  for datum in METADATA:
    if not info.has_key(datum):
      info[datum] = 'none'
  add_to_db(info, app.DB)
  return 'success'

@app.route('/lookup', methods=['GET', 'POST'])
def lookup_gps():
  coords = [(request.json['lat'], request.json['lon'])]
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
