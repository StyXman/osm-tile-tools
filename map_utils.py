# coding=utf-8

from math import pi,cos,sin,log,exp,atan
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import sqlalchemy.exc
from configparser import ConfigParser
import os.path
from os.path import dirname, basename, join as path_join
from os import listdir, stat, unlink, mkdir, walk, makedirs
from errno import ENOENT, EEXIST
from shutil import copy, rmtree
import datetime
import errno

DEG_TO_RAD = pi/180
RAD_TO_DEG = 180/pi

def minmax (a,b,c):
    a = max(a,b)
    a = min(a,c)
    return a

class GoogleProjection:
    def __init__(self,levels=18):
        self.Bc = []
        self.Cc = []
        self.zc = []
        self.Ac = []
        c = 256
        for d in range(0,levels):
            e = c/2
            self.Bc.append(c/360.0)
            self.Cc.append(c/(2 * pi))
            self.zc.append((e,e))
            self.Ac.append(c)
            c *= 2

    def fromLLtoPixel(self,ll,zoom):
        d = self.zc[zoom]
        e = round(d[0] + ll[0] * self.Bc[zoom])
        f = minmax(sin(DEG_TO_RAD * ll[1]),-0.9999,0.9999)
        g = round(d[1] + 0.5*log((1+f)/(1-f))*-self.Cc[zoom])
        return (e,g)

    def fromPixelToLL(self,px,zoom):
        e = self.zc[zoom]
        f = (px[0] - e[0])/self.Bc[zoom]
        g = (px[1] - e[1])/-self.Cc[zoom]
        h = RAD_TO_DEG * ( 2 * atan(exp(g)) - 0.5 * pi)
        return (f,h)


def is_empty (data):
    # TODO: this is *completely* style dependent!
    return len (data)==103 and data[41:44]=='\xc4\xe2\xe2'

class DiskBackend:
    def __init__ (self, base, *more):
        self.base_dir= base

    def tile_uri (self, z, x, y):
        return os.path.join (self.base_dir, str (z), str (x), str (y)+'.png')

    def store (self, z, x, y, data):
        tile_uri= self.tile_uri (z, x, y)
        makedirs (os.path.dirname (tile_uri))
        f= open (tile_uri, 'w+')
        f.write (data)
        f.close ()

    def exists (self, z, x, y):
        tile_uri= self.tile_uri (z, x, y)
        return os.path.isfile (tile_uri)

    def newer_than (self, z, x, y, date):
        tile_uri= self.tile_uri (z, x, y)
        try:
            return datetime.datetime.fromtimestamp (os.stat (tile_uri).st_mtime)>date
        except OSError as e:
            if e.errno==errno.ENOENT:
                return False
            else:
                raise

    def commit (self):
        # TODO: flush?
        pass

Master= sqlalchemy.ext.declarative.declarative_base ()

#CREATE TABLE map (
   #zoom_level INTEGER,
   #tile_column INTEGER,
   #tile_row INTEGER,
   #tile_id TEXT,
   #grid_id TEXT
#);
#CREATE TABLE grid_key (
    #grid_id TEXT,
    #key_name TEXT
#);
#CREATE TABLE keymap (
    #key_name TEXT,
    #key_json TEXT
#);
#CREATE TABLE grid_utfgrid (
    #grid_id TEXT,
    #grid_utfgrid BLOB
#);
#CREATE TABLE images (
    #tile_data blob,
    #tile_id text
#);
#CREATE TABLE metadata (
    #name text,
    #value text
#);
#CREATE UNIQUE INDEX map_index ON map (zoom_level, tile_column, tile_row);
#CREATE UNIQUE INDEX grid_key_lookup ON grid_key (grid_id, key_name);
#CREATE UNIQUE INDEX keymap_lookup ON keymap (key_name);
#CREATE UNIQUE INDEX grid_utfgrid_lookup ON grid_utfgrid (grid_id);
#CREATE UNIQUE INDEX images_id ON images (tile_id);
#CREATE UNIQUE INDEX name ON metadata (name);
#CREATE VIEW tiles AS
    #SELECT
        #map.zoom_level AS zoom_level,
        #map.tile_column AS tile_column,
        #map.tile_row AS tile_row,
        #images.tile_data AS tile_data
    #FROM map
    #JOIN images ON images.tile_id = map.tile_id;
#CREATE VIEW grids AS
    #SELECT
        #map.zoom_level AS zoom_level,
        #map.tile_column AS tile_column,
        #map.tile_row AS tile_row,
        #grid_utfgrid.grid_utfgrid AS grid
    #FROM map
    #JOIN grid_utfgrid ON grid_utfgrid.grid_id = map.grid_id;
#CREATE VIEW grid_data AS
    #SELECT
        #map.zoom_level AS zoom_level,
        #map.tile_column AS tile_column,
        #map.tile_row AS tile_row,
        #keymap.key_name AS key_name,
        #keymap.key_json AS key_json
    #FROM map
    #JOIN grid_key ON map.grid_id = grid_key.grid_id
    #JOIN keymap ON grid_key.key_name = keymap.key_name;

class KeyValue (Master):
    __tablename__= 'metadata'
    name= sqlalchemy.Column (sqlalchemy.String, primary_key=True)
    value= sqlalchemy.Column (sqlalchemy.String)

class Tile (Master):
    __tablename__= 'tiles'
    # primary key
    __table_args__= (
        sqlalchemy.PrimaryKeyConstraint ('zoom_level', 'tile_column', 'tile_row',
                                         name='z_x_y'),
        )

    # id= sqlalchemy.Column (sqlalchemy.Integer, primary_key=True)
    zoom_level= sqlalchemy.Column (sqlalchemy.Integer)
    tile_column= sqlalchemy.Column (sqlalchemy.Integer)
    tile_row= sqlalchemy.Column (sqlalchemy.Integer)
    tile_data= sqlalchemy.Column (sqlalchemy.LargeBinary)

Session= sqlalchemy.orm.sessionmaker ()

class MBTilesBackend:
    def __init__ (self, base, bounds):
        self.eng= sqlalchemy.create_engine ("sqlite:///%s.mbt" % base, echo=True)
        Master.metadata.create_all (self.eng)
        Session.configure (bind=self.eng)
        self.session= Session ()

        #bounds|-27,62,-11,67.5
        #minzoom|5
        #maxzoom|10
        #name|Ísland
        #version|1.0.0
        #center|-18.7,65,7
        #attribution|Map data © OpenStreetMap CC-BY-SA; NASA SRTM; GLISM Glacier Database; ETOPO1 Bathymetry
        #description|Inspired by the 1975 map of Iceland by the Danish Geodetisk Institut.

        # generate metadata
        try:
            name= KeyValue (name='name', value='Elevation')
            self.session.add (name)
            self.session.commit ()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback ()
        try:
            type_= KeyValue (name='type', value='baselayer')
            self.session.add (type_)
            self.session.commit ()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback ()
        try:
            version= KeyValue (name='version', value='2.30.0')
            self.session.add (version)
            self.session.commit ()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback ()
        try:
            description= KeyValue (name='description', value='My own map')
            self.session.add (description)
            self.session.commit ()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback ()
        try:
            format_= KeyValue (name='format', value='png')
            self.session.add (format_)
            self.session.commit ()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback ()
        try:
            bounds= KeyValue (name='bounds', value=bounds)
            self.session.add (bounds)
            self.session.commit ()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback ()

    def store (self, z, x, y, data):
        t= Tile (zoom_level=z, tile_column=x, tile_row=y, tile_data=data)
        self.session.add (t)

    def commit (self):
        if len (self.session.dirty)>0:
            self.session.commit ()

    def exists (self, z, x, y):
        return self.session.query (sqlalchemy.func.count (Tile.zoom_level)).\
                            filter (Tile.zoom_level==z).\
                            filter (Tile.tile_column==x).\
                            filter (Tile.tile_row==y)[0][0]==1 # 1st col, 1st row

    def close (self):
        self.session.close ()

def coord_range (mn, mx, zoom):
    image_size=256.0
    return ( coord for coord in range (mn, mx+1)
                   if coord >= 0 and coord < 2**zoom )

def bbox (value):
    data= value.split (',')
    for index, deg in enumerate (data):
        try:
            deg= float (deg)
        except ValueError:
            # let's try with x:y[:z]
            d= deg.split (':')
            if len (d)==2:
                d.append ('0')

            deg, mn, sec= [ int (x) for x in d ]
            deg= deg+1/60.0*mn+1/3600.0*sec

        data[index]= deg

    return data

class Map:
    def __init__ (self, bbox, max_z):
        self.bbox= bbox
        ll0 = (bbox[0],bbox[3])
        ll1 = (bbox[2],bbox[1])
        gprj = GoogleProjection(max_z+1)

        self.levels= []
        for z in range (0, max_z+1):
            px0 = gprj.fromLLtoPixel(ll0,z)
            px1 = gprj.fromLLtoPixel(ll1,z)
            # print px0, px1
            self.levels.append (( (int (px0[0]/256), int (px0[1]/256)),
                                  (int (px1[0]/256), int (px1[1]/256)) ))
        # print self.levels

    def __contains__ (self, t):
        if len (t)==3:
            z, x, y= t
            px0, px1= self.levels[z]
            # print (z, px0[0], x, px1[0], px0[1], y, px1[1])
            ans= px0[0]<=x and x<=px1[0]
            # print ans
            ans= ans and px0[1]<=y and y<=px1[1]
            # print ans
        elif len (t)==2:
            z, x= t
            px0, px1= self.levels[z]
            # print (z, px0[0], x, px1[0])
            ans= px0[0]<=x and x<=px1[0]
        else:
            raise ValueError

        return ans

    def iterate_x (self, z):
        px0, px1= self.levels[z]
        return coord_range (px0[0], px1[0], z) # NOTE

    def iterate_y (self, z):
        px0, px1= self.levels[z]
        return coord_range (px0[1], px1[1], z) # NOTE

class Atlas:
    def __init__ (self, sectors):
        self.maps= {}
        c= ConfigParser ()
        c.read ('bboxes.ini')
        self.minZoom= 0
        self.maxZoom= 0

        for sector in sectors:
            bb= bbox (c.get ('bboxes', sector))
            # #4 is the max_z
            if bb[4]>self.maxZoom:
                self.maxZoom= int (bb[4])

        for sector in sectors:
            bb= bbox (c.get ('bboxes', sector))
            self.maps[sector]= Map (bb[:4], self.maxZoom)

    def __contains__ (self, t):
        w= False
        for m in self.maps.values ():
            w= w or t in m

        return w

    def iterate_x (self, z):
        for m in self.maps.values ():
            for x in m.iterate_x (z):
                yield x

    def iterate_y (self, z, x):
        for m in self.maps.values ():
            if (z, x) in m:
                for y in m.iterate_y (z):
                    yield y
