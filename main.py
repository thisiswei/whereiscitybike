#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import webapp2
import math
import os
import jinja2
import json

from google.appengine.api import urlfetch

URL = 'http://ip-api.com/json/'
BIKE_JSON_URL = 'http://citibikenyc.com/stations/json'
GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True) 

def get_dist(lat1, lon1, lat2, lon2):
    phi1 = to_rad(90.0 - lat1)
    phi2 = to_rad(90.0 - lat2)
    theta1 = to_rad(lon1)
    theta2 = to_rad(lon2)
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos(cos)
    return arc

def to_rad(n):
    return n * math.pi / 180

def get_lat_lon(json_, lat, lon):
    return float(json_.get(lat)), float(json_.get(lon))

def get_json(url):
    resp = urlfetch.fetch(url)
    return json.loads(resp.content)


class MainHandler(webapp2.RequestHandler):
    def render(self, template, **parms):
        t = jinja_env.get_template(template)
        return self.response.write(t.render(parms))

class GetStation(MainHandler):
    def get(self):
        stations = self.get_stations()
        user_lat_lon = self.get_user_geos()
        closest = self.get_closest_station(stations, user_lat_lon)
        closest_lat_lon = get_lat_lon(closest, 'latitude', 'longitude')
        addr = closest.get('stAddress1')
        self.render('index.html', user_lat_long=user_lat_lon,
                    closest_lat_lon=closest_lat_lon, addr=addr)

    def get_closest_station(self, stations, user_lat_lon):
        user_lat, user_lon = user_lat_lon
        closest = min(stations,
                      key=lambda x: get_dist(float(x.get('latitude')),
                                             float(x.get('longitude')),
                                             user_lat, user_lon))
        return closest

    def get_stations(self):
        json_ = get_json(BIKE_JSON_URL)
        stations = json_.get('stationBeanList')
        return stations

    def get_user_geos(self):
        ip = self.request.remote_addr
        url = URL + ip
        json_ = get_json(url)
        lat, lon = get_lat_lon(json_, 'lat', 'lon')
        return lat, lon


app = webapp2.WSGIApplication([
    ('/', GetStation)
], debug=True)
