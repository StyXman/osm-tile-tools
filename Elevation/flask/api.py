from flask import Flask, request
from flask_restful import abort, Api, Resource
from model import Trip, session

app= Flask (__name__)
api= Api (app)


CORPSE= { 'Access-Control-Allow-Origin': '*' }

class TripController (Resource):

    def get (self, name):
        # GET     http://[hostname]/trips/[name]
        trip= session.query (Trip).filter_by (name=name).first ()

        return trip.toJson (), 200, CORPSE

    def put (self, name):
        # PUT     http://[hostname]/trips/[name]
        trip= session.query (Trip).filter_by (name=name).first ()
        trip.updatePoints (request.form['trip'])

        session.add (trip)
        session.commit ()

        return trip.toJson (), 201, CORPSE

    # POST    http://[hostname]/trips/[name]
    def post (self, name):
        """This method extends the RESTful convention to implement UPSERT"""
        q= session.query (Trip).filter_by (name=name)
        if q.count ()==0:
            # INSERT
            trip= Trip.fromJson (request.form['trip'])
        else:
            # UPDATE
            trip= q.first ()
            trip.updatePoints (request.form['trip'])

        session.add (trip)
        session.commit ()

        return trip.toJson (), 201, CORPSE

    # TODO:
    # DELETE  http://[hostname]/trips/[name]

# this is kinda silly
class TripsController (Resource):

    def get (self):
        # GET     http://[hostname]/trips
        trips= session.query (Trip).all ()
        return [ trip.toJson () for trip in trips ], 200, CORPSE

    # POST    http://[hostname]/trips
    def post (self):
        # trip={ "name": "default", "points": [ [ 43.55277819471542, 6.934947967529298 ], [ 43.581136968065685, 6.942672729492188 ] ] }
        trip= Trip.fromJson (request.form['trip'])
        session.add (trip)
        session.commit ()
        return trip.toJson (), 201, CORPSE


api.add_resource (TripController, '/trips/<name>')
api.add_resource (TripsController, '/trips')

if __name__=='__main__':
    app.run (host='0.0.0.0', debug=True)
