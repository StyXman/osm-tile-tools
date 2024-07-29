# coding=utf-8

from math import pi, cos, sin, log, exp, atan
from configparser import ConfigParser
import os.path
from os.path import dirname, basename, join as path_join
from os import listdir, unlink, mkdir, walk, makedirs
import os
from errno import ENOENT, EEXIST
from shutil import copy, rmtree
import datetime
import errno
import hashlib
import sqlite3
import stat

from shapely.geometry import Polygon
from shapely import wkt

from tiles import GoogleProjection, Tile, MetaTile, PixelTile

from logging import debug
from typing import List, Tuple, Dict, Optional, Any, Union


def constrain(lower_limit:float, x:float, upper_limit:float) -> float:
    """Constrains x to the [lower_limit, upper_limit] segment."""
    ans = max(lower_limit, x)
    ans = min(ans, upper_limit)

    return ans


# helper types
TileOrTuple = Union[Tile, Tuple[int, int, int]]

class DiskBackend:
    fs_based = True

    def __init__(self, base:str, *more, **even_more):
        self.base_dir = base
        self.filename_pattern = even_more.get('filename_pattern',
                                              '{base_dir}/{z}/{x}/{y}.png')


    def tile_uri(self, tile: TileOrTuple) -> str:
        # this works because I made Tile iterable
        z, x, y = ( str(i) for i in tile )
        base_dir = self.base_dir

        return self.filename_pattern.format(**locals())


    def store(self, tile: Tile):
        assert tile.data is not None

        tile_uri = self.tile_uri(tile)
        makedirs(os.path.dirname(tile_uri), exist_ok=True)
        f = open(tile_uri, 'wb+')
        f.write(tile.data)
        f.close()


    def exists(self, tile: TileOrTuple):
        tile_uri = self.tile_uri(tile)
        return os.path.isfile(tile_uri)


    def fetch(self, tile: Tile):
        tile_uri = self.tile_uri(tile)
        try:
            print(tile_uri)
            f = open(tile_uri, 'br')
        except OSError as e:
            print(e)
            return False
        else:
            tile.data = f.read()
            f.close()

            return True


    def newer_than(self, tile: TileOrTuple, date, missing_as_new):
        tile_uri = self.tile_uri(tile)
        try:
            file_date = datetime.datetime.fromtimestamp(os.stat(tile_uri).st_mtime)
            # debug("%s: %s <-> %s", tile_uri, file_date.isoformat(),
            #       date.isoformat())
            return file_date > date
        except OSError as e:
            if e.errno == errno.ENOENT:
                # debug("%s: %s", tile_uri, missing_as_new)
                return missing_as_new
            else:
                raise


    def commit(self):
        # TODO: flush?
        pass


    def __contains__(self, tile: TileOrTuple):
        return self.exists(tile)


class ModTileBackend(DiskBackend):
    def tile_uri(self, tile: TileOrTuple):
        # The metatiles are then stored
        # in the following directory structure:
        # /[base_dir]/[TileSetName]/[Z]/[xxxxyyyy]/[xxxxyyyy]/[xxxxyyyy]/[xxxxyyyy]/[xxxxyyyy].png
        # Where base_dir is a configurable base path for all tiles. TileSetName
        # is the name of the style sheet rendered. Z is the zoom level.
        # [xxxxyyyy] is an 8 bit number, with the first 4 bits taken from the x
        # coordinate and the second 4 bits taken from the y coordinate. This
        # attempts to cluster 16x16 square of tiles together into a single sub
        # directory for more efficient access patterns.
        z, x, y = tile

        crumbs: List[str] = []
        for crumb_index in range(5):
            x, x_bits = divmod(x, 16)
            y, y_bits = divmod(y, 16)
            debug((x, x_bits, y, y_bits))

            crumb = (x_bits << 4) + y_bits
            crumbs.insert(0, str(crumb))

        return os.path.join(self.base_dir, str(z), *crumbs[:-1], crumbs[-1] + '.png')


class TestBackend(DiskBackend):
    def __init__(self, base:str, *more, **even_more):
        self.base_dir = base
        self.filename_pattern = even_more.get('filename_pattern',
                                              '{base_dir}/{z}-{x}-{y}.png')


# https://github.com/mapbox/node-mbtiles/blob/master/lib/schema.sql
# https://github.com/mapbox/mbutil/blob/master/mbutil/util.py

# according to the spec https://github.com/mapbox/mbtiles-spec/blob/master/1.2/spec.md
# the schemas outlined are meant to be followed as interfaces.
# SQLite views that produce compatible results are equally valid.
# For convenience, this specification refers to tables and virtual tables (views) as tables.

# so what happens with the tiles tables is exactly that:
# it's implemented as a (read only) view on top of map an images
# but internally we fill them separately

class MBTilesBackend:
    fs_based = False

    # .sqlitedb 'cause I'll use it primarily for OsmAnd
    def __init__(self, path, bounds, min_zoom=0, max_zoom=18, center=None, ro=False):
        self.path = path

        if ro:
            spec = 'file:' + self.path + '?mode=ro'
            # print(spec)
            self.session = sqlite3.connect(spec, uri=True)
        else:
            self.session = sqlite3.connect(self.path)
        self.session.set_trace_callback(print)

        if not stat.S_ISREG(os.stat(self.path).st_mode):
            # create the db
            self.init()


    def init(self):
        cursor = self.session.cursor()
        # mbtiles
        cursor.execute('''CREATE TABLE IF NOT EXISTS metadata(
            name    VARCHAR NOT NULL,
            value   VARCHAR,
            PRIMARY KEY (name)
        );''')

        # OsmAnd
        # see https://github.com/osmandapp/Osmand/blob/master/OsmAnd/src/net/osmand/plus/SQLiteTileSource.java#L179
        # and https://osmand.net/help-online/technical-articles#OsmAnd_SQLite_Spec
        cursor.execute('''CREATE TABLE IF NOT EXISTS info(
            -- all these are optional
            -- rule           VARCHAR,
            -- referer        VARCHAR,
            -- timecolumn     VARCHAR,
            -- expireminutes  INTEGER,
            -- ellipsoid      INTEGER,
            url            VARCHAR,
            -- this one is important so we don't get constrained by BigPlanet,
            -- which has max_z == 17
            tilenumbering  VARCHAR,
            minzoom        INTEGER NOT NULL,
            maxzoom        INTEGER NOT NULL
        );''')

        # common
        cursor.execute('''CREATE TABLE IF NOT EXISTS map(
            zoom_level   INTEGER NOT NULL,
            tile_column  INTEGER NOT NULL,
            tile_row     INTEGER NOT NULL,
            tile_id      VARCHAR(32),
            CONSTRAINT map_index PRIMARY KEY (zoom_level, tile_column, tile_row)
        );''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS images(
            tile_id    VARCHAR(32) NOT NULL,
            tile_data  BLOB,
            PRIMARY KEY (tile_id)
        );''')

        # see https://gist.github.com/rzymek/034ef469fa01fdd592a6aadde76e95fa
        # just ignore the info about inverted y/tile_row
        cursor.execute('''CREATE VIEW IF NOT EXISTS tiles AS
            SELECT
                -- mbtiles
                map.zoom_level    AS zoom_level,
                map.tile_column   AS tile_column,
                map.tile_row      AS tile_row,
                images.tile_data  AS tile_data,

                -- OsmAnd
                map.zoom_level    AS z,
                map.tile_column   AS x,
                map.tile_row      AS y,
                0                 AS s,  -- TODO: check where does this 's' come from
                images.tile_data  AS image
            FROM
                map JOIN images
                    ON images.tile_id = map.tile_id;''')

        self.session.commit()

        #version|1.0.0
        #center|-18.7,65,7
        #attribution|Map data © OpenStreetMap CC-BY-SA; NASA SRTM; GLISM Glacier Database; ETOPO1 Bathymetry
        #description|Inspired by the 1975 map of Iceland by the Danish Geodetisk Institut.

        # generate metadata
        metadata = dict(
            name ='Elevation',
            type ='baselayer',
            version ='2.39.0-04f6d1b',  # I wonder why git uses only 7 chars by default
            description ="StyXman's simple map",
            format ='png',
            bounds =','.join([ str(i) for i in bounds ]),
            attribution ='Map data © OpenStreetMap CC-BY-SA; NASA SRTM',
        )

        for k, v in metadata.items():
            try:
                cursor.execute('''INSERT INTO metadata(name, value) VALUES (?, ?);''',
                               (k, v))
            except sqlite3.IntegrityError:
                cursor.execute('''UPDATE metadata SET value = ? WHERE name = ?;''',
                               (v, k))

        # info for OsmAnd
        cursor.execute('''INSERT INTO info(url, tilenumbering, minzoom, maxzoom) VALUES (?, ?, ?, ?);''',
                       ("http://dionecanali.hd.free.fr/~mdione/Elevation/$1/$2/$3.png", "normal",
                        min_zoom, max_zoom))

        # TODO: replace by (1 << 8) -1 ?
        for z in range(max_zoom + 1):
            cursor.execute('''INSERT INTO max_y(z, y) VALUES (?, ?);''', (z, 2**z - 1))

        self.session.commit()
        self.session.set_trace_callback(None)

        cursor.close()


    def store (self, tile: Tile):
        assert tile.data is not None

        self.store_raw(tile.z, tile.x, tile.y, tile.data)


    def store_raw (self, z: int, x: int, y: int, image: bytes):
        # create one of these each time because there's no way to reset them
        # and barely takes any time
        hasher = hashlib.md5()

        # md5 gives 340282366920938463463374607431768211456 possible values
        # and is *fast*
        hasher.update(image)

        # thanks Pablo Carranza for pointing out possible collisions
        # further deduplicate with file length
        hasher.update(str(len(image)).encode('ascii'))
        img_id = hasher.hexdigest()

        debug((tile, img_id))

        cursor = self.session.cursor ()
        try:
            cursor.execute ('''INSERT INTO images (tile_id, tile_data) VALUES (?, ?);''',
                            (img_id, image))
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


    def exists (self, tile: TileOrTuple):
        cursor= self.session.cursor ()
        data= cursor.execute('''SELECT count(map.zoom_level)
                                FROM map
                                WHERE map.zoom_level = ?
                                  AND map.tile_column = ?
                                  AND map.tile_row = ?;''',
                             tuple(tile)).fetchall()

        return data[0][0] == 1


    def fetch(self, tile: Tile):
        print(tile)
        cursor = self.session.cursor()
        data = cursor.execute('''SELECT tile_data
                                 FROM tiles
                                 WHERE tiles.z = ?
                                   AND tiles.x = ?
                                   AND tiles.y = ?;''',
                              tuple(tile)).fetchall()

        if len(data) == 0:
            return False

        tile.data = data[0][0]
        return True


    # TODO: newer_than()


    def close (self):
        self.session.close ()


    def __contains__(self, tile: TileOrTuple):
        return self.exists(tile)


def coord_range(mn, mx, zoom):
    return ( coord for coord in range(mn, mx + 1)
                   if coord >= 0 and coord < 2**zoom )


def bbox(value):
    data = value.split(',')
    for index, deg in enumerate(data):
        try:
            deg = float(deg)
        except ValueError:
            # let's try with x:y[:z]
            d = deg.split(':')
            if len(d) == 2:
                d.append('0')

            deg, mn, sec = [ int(x) for x in d ]
            deg = deg + 1/60.0*mn + 1/3600.0*sec

        data[index] = deg

    return data


class BBox:
    def __init__(self, bbox, max_z):
        self.w, self.s, self.e, self.n = bbox
        self.max_z = max_z
        self.proj = GoogleProjection(self.max_z+1)  # +1

        # it's LonLat! (x, y)
        self.upper_left = (self.w, self.n)
        self.lower_left = (self.w, self.s)
        self.upper_right = (self.e, self.n)
        self.lower_right = (self.e, self.s)

        # in degrees
        self.boundary = Polygon([ self.upper_left, self.lower_left,
                                  self.lower_right, self.upper_right,
                                  self.upper_left])


    def __contains__(self, tile):
        other = tile.polygon

        debug((other.wkt, self.boundary.wkt))
        return other.intersects(self.boundary)


    def __repr__(self):
        return "BBox(%f, %f, %f, %f, %d)" % (self.w, self.s, self.e, self.n,
                                             self.max_z)


    # TODO: see if it doesn't make more sense to work everything at pixel level


class Map:
    def __init__ (self, bbox, max_z):
        self.bbox = bbox
        self.max_z = max_z
        # TODO:
        self.tile_size = 256

        ll0 = (bbox[0],bbox[3])
        ll1 = (bbox[2],bbox[1])
        gprj = GoogleProjection(max_z+1)

        self.levels = []
        for z in range (0, max_z+1):
            px0 = gprj.lon_lat2pixel(ll0,z)
            px1 = gprj.lon_lat2pixel(ll1,z)
            # print px0, px1
            self.levels.append (( (int (px0[0]/self.tile_size), int (px0[1]/self.tile_size)),
                                  (int (px1[0]/self.tile_size), int (px1[1]/self.tile_size)) ))


    def __contains__ (self, t):
        if len (t) == 3:
            z, x, y = t
            px0, px1= self.levels[z]
            # print (z, px0[0], x, px1[0], px0[1], y, px1[1])
            ans = px0[0] <= x and x <= px1[0]
            # print ans
            ans = ans and px0[1] <= y and y <= px1[1]
            # print ans
        elif len (t) == 2:
            z, x = t
            px0, px1 = self.levels[z]
            # print (z, px0[0], x, px1[0])
            ans = px0[0] <= x and x <= px1[0]
        else:
            raise ValueError

        return ans


    def iterate_x (self, z):
        px0, px1 = self.levels[z]
        return coord_range(px0[0], px1[0], z) # NOTE


    def iterate_y (self, z):
        px0, px1 = self.levels[z]
        return coord_range(px0[1], px1[1], z) # NOTE


class Atlas:
    def __init__(self, maps):
        self.maps = {}
        atlas_config = ConfigParser()
        atlas_config.read('atlas.ini')
        self.minZoom = 0
        self.maxZoom = 0

        for map in maps:
            bb = bbox(atlas_config.get('maps', map))
            # #4 is the max_z
            if bb[4] > self.maxZoom:
                self.maxZoom = int(bb[4])

        for map in maps:
            bb= bbox (atlas_config.get ('maps', map))
            self.maps[map]= Map (bb[:4], self.maxZoom)


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


def test_all():
    # import logging
    # logging.basicConfig(level=logging.DEBUG)

    # Europe
    b = BBox((-10, 35, 30, 60), 18)

    def test(bbox, z, expected):
        # it's a square
        tiles = len(expected)
        for x in range(tiles):
            for y in range(tiles):
                t = Tile(z, x, y)
                result = t in bbox
                # NOTE: if you look at how expected is defined, this is the
                # right order of 'coords'
                if result != expected[y][x]:
                    if expected[x][y]:
                        raise AssertionError("%r not in %r" % (t, bbox))
                    else:
                        raise AssertionError("%r in %r" % (t, bbox))

    # ZL0
    expected = [ [ True ] ]
    test(b, 0, expected)

    # ZL1
    expected = [ [ True,  True  ],
                 [ False, False ] ]
    test(b, 1, expected)

    # ZL2
    expected = [ [ False, False, False, False ],
                 [ False, True,  True , False ],
                 [ False, False, False, False ],
                 [ False, False, False, False ] ]
    test(b, 2, expected)

    # ZL3
    expected = [ [ False, False, False, False, False, False, False, False ],
                 [ False, False, False, False, False, False, False, False ],
                 [ False, False, False, True,  True , False, False, False ],
                 [ False, False, False, True,  True , False, False, False ],
                 [ False, False, False, False, False, False, False, False ],
                 [ False, False, False, False, False, False, False, False ],
                 [ False, False, False, False, False, False, False, False ],
                 [ False, False, False, False, False, False, False, False ] ]
    test(b, 3, expected)

    g = GoogleProjection(18)
    for z in range(19):
        side = 256 * 2**z
        middle = side // 2

        x, y = g.lon_lat2pixel((0, 0), z)

        assert x == middle
        assert y == middle

        lon, lat = g.pixel2lon_lat((x, y), z)

        assert lon == 0
        assert lat == 0

    print('A-OK')


if __name__ == '__main__':
    test_all()
