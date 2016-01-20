from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy_utils import ScalarListType

engine= create_engine ('sqlite:///trip_planner.sqlite3')

Tables= declarative_base ()

class Trip (Tables):
    __tablename__= 'trips'

    id= Column (Integer, primary_key=True)
    name= Column (String)
    points= Column (ScalarListType(float))

Tables.metadata.create_all (engine)

Session= sessionmaker (bind=engine)
session= Session ()
