from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from model import Trip, session
import itertools

app= Flask (__name__)
api= Api (app)

# taken from itertools' doc
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

parser= reqparse.RequestParser ()
parser.add_argument ('name')
parser.add_argument ('coord', type=float, action='append')

class TripController (Resource):
    def get (self, name):
        trip= session.query (Trip).filter_by (name=name).first ()
        points= [ (x, y) for x, y in grouper (trip.points, 2) ]

        return { 'name': trip.name, 'points': points }

api.add_resource (TripController, '/trip/<name>')

if __name__=='__main__':
    app.run (debug=True)
