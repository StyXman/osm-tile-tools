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

    # POST    http://[hostname]/trips
    def post (self):
        # trip={ "name": "default", "points": [ [ 43.55277819471542, 6.934947967529298 ], [ 43.581136968065685, 6.942672729492188 ] ] }
        trip= Trip.fromJson (request.form['trip'])
        session.add (trip)
        session.commit ()
        return trip.toJson (), 201


api.add_resource (TripController, '/trips/<name>')
api.add_resource (TripsController, '/trips')

if __name__=='__main__':
    app.run (debug=True)
