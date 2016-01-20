from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from model import Trip, session

app= Flask (__name__)
api= Api (app)


parser= reqparse.RequestParser ()
parser.add_argument ('name')
parser.add_argument ('coord', type=float, action='append')

class TripController (Resource):
    def get (self, name):
        trip= session.query (Trip).filter_by (name=name).first ()

        return trip.toJson ()

api.add_resource (TripController, '/trip/<name>')

if __name__=='__main__':
    app.run (debug=True)
