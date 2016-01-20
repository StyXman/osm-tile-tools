from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from model import Trip, session

app= Flask (__name__)
api= Api (app)

# Method  URI     Action
# PUT     http://[hostname]/trips/[name]
# DELETE  http://[hostname]/trips/[name]

parser= reqparse.RequestParser ()
parser.add_argument ('name')
parser.add_argument ('coord', type=float, action='append')

class TripController (Resource):
    def get (self, name):
        # GET     http://[hostname]/trips/[name]
        trip= session.query (Trip).filter_by (name=name).first ()

        return trip.toJson ()

# this is kinda silly
class TripsController (Resource):

    def get (self):
        # GET     http://[hostname]/trips
        trips= session.query (Trip).all ()
        return [ trip.toJson () for trip in trips ]

api.add_resource (TripController, '/trips/<name>')
api.add_resource (TripsController, '/trips')

if __name__=='__main__':
    app.run (debug=True)
