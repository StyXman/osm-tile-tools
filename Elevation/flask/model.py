from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy_utils import ScalarListType
import itertools

engine= create_engine ('sqlite:///trip_planner.sqlite3')

Tables= declarative_base ()

# taken from itertools' doc
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

class Trip (Tables):
    __tablename__= 'trips'

    id= Column (Integer, primary_key=True)
    name= Column (String)
    points= Column (ScalarListType(float))

    def toJson (self):
        """Convert a Trip to a dict representing the trip.
        Notice that the points is converted from a list of floats to alist of tuples of floats.
        Notice too that it is not converted to a string."""

        points= [ (x, y) for x, y in grouper (self.points, 2) ]

        return { 'name': self.name, 'points': points }

Tables.metadata.create_all (engine)

Session= sessionmaker (bind=engine)
session= Session ()
