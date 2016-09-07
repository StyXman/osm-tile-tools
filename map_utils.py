# coding=utf-8

from math import pi,cos,sin,log,exp,atan
from configparser import ConfigParser
import os.path
from os.path import dirname, basename, join as path_join
from os import listdir, stat, unlink, mkdir, walk, makedirs
from errno import ENOENT, EEXIST
from shutil import copy, rmtree
import datetime
import errno
import hashlib
import sqlite3

from logging import debug


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
    return len (data)==103 and data[41:44]==b'\xb5\xd0\xd0'

class DiskBackend:
    def __init__ (self, base, *more):
        self.base_dir= base

    def tile_uri (self, z, x, y):
        return os.path.join (self.base_dir, str (z), str (x), str (y)+'.png')

    def store (self, z, x, y, data):
        tile_uri= self.tile_uri (z, x, y)
        makedirs (os.path.dirname (tile_uri), exist_ok=True)
        f= open (tile_uri, 'wb+')
        f.write (data)
        f.close ()

    def exists (self, z, x, y):
        tile_uri= self.tile_uri (z, x, y)
        return os.path.isfile (tile_uri)

    def newer_than (self, z, x, y, date):
        tile_uri= self.tile_uri (z, x, y)
        try:
            file_date= datetime.datetime.fromtimestamp (os.stat (tile_uri).st_mtime)
            debug ("%s <-> %s", file_date.isoformat (), date.isoformat ())
            return file_date > date
        except OSError as e:
            if e.errno==errno.ENOENT:
                return False
            else:
                raise

    def commit (self):
        # TODO: flush?
        pass

# https://github.com/mapbox/node-mbtiles/blob/master/lib/schema.sql
# https://github.com/mapbox/mbutil/blob/master/mbutil/util.py

# according to the spec https://github.com/mapbox/mbtiles-spec/blob/master/1.2/spec.md
# the schemas outlined are meant to be followed as interfaces.
# SQLite views that produce compatible results are equally valid.
# For convenience, this specification refers to tables and virtual tables (views) as tables.

# so what happens with the tiles tables is exactly that:
# it's implemented as a (read only) view on top of map an images
# but internally we fill tem separately

class MBTilesBackend:
    def __init__ (self, base, bounds):
        self.session= sqlite3.connect ("%s.mbt" % base)
        self.session.set_trace_callback (print)

        cursor= self.session.cursor ()
        cursor.execute ('''CREATE TABLE IF NOT EXISTS metadata (
            name VARCHAR NOT NULL,
            value VARCHAR,
            PRIMARY KEY (name)
        );''')
        cursor.execute ('''CREATE TABLE IF NOT EXISTS map (
            zoom_level INTEGER NOT NULL,
            tile_column INTEGER NOT NULL,
            tile_row INTEGER NOT NULL,
            tile_id VARCHAR(32),
            CONSTRAINT map_index PRIMARY KEY (zoom_level, tile_column, tile_row)
        );''')
        cursor.execute ('''CREATE TABLE IF NOT EXISTS images (
            tile_id VARCHAR(32) NOT NULL,
            tile_data BLOB,
            PRIMARY KEY (tile_id)
        );''')
        cursor.execute ('''CREATE VIEW IF NOT EXISTS tiles AS
            SELECT
                map.zoom_level AS zoom_level,
                map.tile_column AS tile_column,
                map.tile_row AS tile_row,
                images.tile_data AS tile_data
            FROM
                map JOIN images
                    ON images.tile_id = map.tile_id;''')
        self.session.commit ()

        #bounds|-27,62,-11,67.5
        #minzoom|5
        #maxzoom|10
        #name|Ísland
        #version|1.0.0
        #center|-18.7,65,7
        #attribution|Map data © OpenStreetMap CC-BY-SA; NASA SRTM; GLISM Glacier Database; ETOPO1 Bathymetry
        #description|Inspired by the 1975 map of Iceland by the Danish Geodetisk Institut.

        # generate metadata
        metadata= dict(
            name='Elevation',
            type='baselayer',
            version='2.39.0-04f6d1b',  # I wonder why git uses only 7 chars by default
            description="StyXman's simple map",
            format='png',
            bounds=','.join ([ str (i) for i in bounds ]),
            attribution='Map data © OpenStreetMap CC-BY-SA; NASA SRTM',
            )

        for k, v in metadata.items ():
            try:
                cursor.execute ('''INSERT INTO metadata (name, value) VALUES (?, ?);''',
                                (k, v))
            except sqlite3.IntegrityError:
                cursor.execute ('''UPDATE metadata SET value = ? WHERE name = ?;''',
                                (v, k))
        self.session.commit ()

        cursor.close ()


    def store (self, z, x, y, data):
        # create one of these each time because there's no way to reset them
        # and barely takes any time
        hasher= hashlib.md5 ()
        # md5 gives 340282366920938463463374607431768211456 possible values
        # and is *fast*
        hasher.update (data)
        # thanks Pablo Carranza for pointing out possible collisions
        # further deduplicate with file length
        hasher.update (str (len (data)).encode ('ascii'))
        img_id= hasher.hexdigest ()

        print (z, x, y, img_id)


        cursor= self.session.cursor ()
        try:
            cursor.execute ('''INSERT INTO images (tile_id, tile_data) VALUES (?, ?);''',
                            (img_id, data))
        except sqlite3.IntegrityError:
            # it already exists and there's no reason to try to update anything
            pass

        try:
            cursor.execute ('''INSERT INTO map (zoom_level, tile_column, tile_row, tile_id)
                                VALUES (?, ?, ?, ?);''',
                            (z, x, y, img_id))
        except sqlite3.IntegrityError:
            cursor.execute ('''UPDATE map
                                SET tile_id = ?
                                WHERE zoom_level = ?
                                  AND tile_column = ?
                                  AND tile_row = ?;''',
                            (img_id, z, x, y))
        cursor.close ()



    def commit (self):
        if self.session.in_transaction:
            self.session.commit ()


    def exists (self, z, x, y):
        cursor= self.session.cursor ()
        data= cursor.execute ('''SELECT count(map.zoom_level)
                                 FROM map
                                 WHERE map.zoom_level = ?
                                   AND map.tile_column = ?
                                   AND map.tile_row = ?;''',
                              (z, x, y)).fetchall ()
        return data[0][0]==1


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
        self.max_z= max_z

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
