import os
import shutil

from datetime import datetime
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import requests


app = Flask(__name__)
CORS(app)
cache_dir = 'cache'
base_url = 'http://rammb-slider.cira.colostate.edu/data/'
json_url = '{}/json/'.format(base_url)
imagery_url = '{}/imagery/'.format(base_url)

latest_json = None
latest_json_date = None
latest_json_expires = 15*60  # 15 minutes

@app.after_request
def add_header(response):
    response.cache_control.max_age = 300
    return response

@app.route('/latest')
def latest():
    global latest_json, latest_json_date, latest_json_expires
    now = datetime.utcnow()

    # rudimentary in-memory cache
    if latest_json and (now - latest_json_date).total_seconds() < latest_json_expires:
        return jsonify(latest_json)

    full_url = '{}{}'.format(json_url, 'goes-16/full_disk/geocolor/latest_times.json')
    response = requests.get(full_url)

    if 200 <= response.status_code < 300:
        # save cache
        latest_json = response.json()
        latest_json_date = now

        return jsonify(latest_json)

    # not sure what happened, just forward the response
    return response

@app.route('/imagery/<path:url>')
def mirror(url):
    # super duper disk cache
    # check if the file exists in the cache folder
    filepath = os.path.join(cache_dir, url)

    if not (os.path.isfile(filepath) and os.stat(filepath).st_size > 0):
        # didn't exist in the cache folder, so try to fetch it
        full_url = '{}{}'.format(imagery_url, url)
        response = requests.get(full_url, stream=True)
        if 200 <= response.status_code < 300:
            # make sure the dir exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            # save the file
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(response.raw, f)

    return send_from_directory(cache_dir, url)
