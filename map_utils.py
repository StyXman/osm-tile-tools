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

from logging import debug
from typing import List, Tuple, Dict, Optional, Any, Union


# DEG_TO_RAD:float = pi / 180
# RAD_TO_DEG:float = 180 / pi
DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi


def constrain(lower_limit:float, x:float, upper_limit:float) -> float:
    """Constrains x to the [lower_limit, upper_limit] segment."""
    ans = max(lower_limit, x)
    ans = min(ans, upper_limit)

    return ans


class GoogleProjection:
    """This class converts from LonLat to pixel and vice versa. For that, it pre
    calculates some values for each zoom level, which are store in 3 arrays.

    For information about the formulas in lon_lat2pixel() and pixel2lon_lat(), see
    https://en.wikipedia.org/wiki/Mercator_projection#Mathematics_of_the_Mercator_projection"""
    def __init__(self, levels:int=18) -> None:
        self.pixels_per_degree:List[float] = []
        self.pixels_per_radian:List[float] = []  # pixels per radian
        self.center_pixel:List[Tuple[int, int]] = []  # pixel for (0, 0)
        # self.world_size:List[int] = []  # world size in pixels

        world_size:int = 256  # size in pixels of the image representing the whole world
        for d in range(levels + 1): # type: int
            center:int = world_size // 2
            self.pixels_per_degree.append(world_size / 360.0)
            self.pixels_per_radian.append(world_size / (2 * pi))
            self.center_pixel.append((center, center))
            # self.world_size.append(c)
            # the world doubels in size on each zoom level
            world_size *= 2

    # it's LonLat! (lon, lat)
    def lon_lat2pixel(self, lon_lat:Tuple[float, float], zoom:int) -> Tuple[int, int]:
        lon, lat = lon_lat
        center_x, center_y = self.center_pixel[zoom]

        # x is easy because it's linear to the longitude
        x = center_x + round(lon * self.pixels_per_degree[zoom])

        # y is... what?
        f = constrain(-0.9999, sin(DEG_TO_RAD * lat), 0.9999)
        y = center_y + round(0.5 * log((1 + f) / (1 - f)) * -self.pixels_per_radian[zoom])

        return (x, y)

    def pixel2lon_lat(self, px:Tuple[int, int], zoom:int) -> Tuple[float,float]:
        x, y = px
        center_x, center_y = self.center_pixel[zoom]

        # longitude is linear to x
        lon = (x - center_x) / self.pixels_per_degree[zoom]

        angle = (y - center_y) / -self.pixels_per_radian[zoom]  # angle in radians
        lat = RAD_TO_DEG * (2 * atan(exp(angle)) - 0.5 * pi)

        return (lon, lat)

class Tile:
    # def __init__(self, z:int, x:int, y:int, metatile:Optional[MetaTile]=None) -> None:
    def __init__(self, z:int, x:int, y:int, metatile=None) -> None:
        self.z = z
        self.x = x
        self.y = y

        # self.meta_index:Optional[Tuple[int, int]] = None
        self.meta_index = None
        self.meta_pixel_coords = None
        if metatile is not None:
            self.meta_index = (x - metatile.x, y - metatile.y)
            self.meta_pixel_coords = ()
            self.tile_size = metatile.tile_size
        else:
            # TODO: guessed
            self.tile_size = 256

        self.pixel_pos = (self.x * self.tile_size, self.y * self.tile_size)
        self.image_size = (self.tile_size, self.tile_size)
        self.data: Optional[bytes] = None
        self._is_empty = None  # Optional[bool]


    def __eq__(self, other):
        return ( self.z == other.z and self.x == other.x and self.y == other.y )


    def __repr__(self):
        return "Tile(%d, %d, %d, %r)" % (self.z, self.x, self.y, self.meta_index)


    @property
    def is_empty(self):
        if self._is_empty is None:
            # TODO: this is *completely* style dependent!
            self._is_empty = ( len(self.data) == 103 and
                               self.data[41:44] == b'\xb5\xd0\xd0' )

        return self._is_empty


    def __iter__(self):
        return self.iter()


    def iter(self):
        """Returns a generator over the 'coords'."""
        yield self.z
        yield self.x
        yield self.y


# helper types
TileOrTuple = Union[Tile, Tuple[int, int, int]]

class DiskBackend:
    fs_based = True

    def __init__(self, base:str, *more):
        self.base_dir = base


    def tile_uri(self, tile: TileOrTuple) -> str:
        # this works because I made Tile iterable
        z, x, y = ( str(i) for i in tile )

        return os.path.join(self.base_dir, z, x, y + '.png')


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
    def tile_uri(self, tile):
        z, x, y = ( str(i) for i in tile )

        return os.path.join(self.base_dir, '-'.join([ z, x, y + '.png' ]))


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
                0                 AS s,  -- TODO: check where does this s come from
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
    return ( coord for coord in range(mn, mx+1)
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


def tile_spec2zxy(tile_spec):  # str -> Tuple[int, int, int]
    try:
        if ',' in tile_spec:
            data = tile_spec.split(',')
        elif '/' in tile_spec:
            data = tile_spec.split('/')
        else:
            raise ValueError
    except ValueError:
        raise ValueError("METATILE not in form Z,X,Y or Z/X/Y.")
    else:
        z, x, y = map(int, data)
        return (z, x, y)


tileproj = GoogleProjection(30)


class PixelTile:
    """It's a (meta) tile with arbitrary pixel bounds."""
    def __init__(self, z, center_x, center_y, size):
        self.z = z
        self.x = center_x
        self.y = center_y

        self.is_empty = False
        self.render = True

        half_size = size // 2
        # (x, y)
        self.pixel_pos = (center_x - half_size, center_y - half_size)
        # debug(self.pixel_pos)
        # (w, h)
        self.image_size = (size, size)
        # debug(self.image_size)

        self.tiles = [ self ]

        # ((x0, y0), (x1, y1))
        self.corners = ( self.pixel_pos,
                         (self.pixel_pos[0] + self.image_size[0],
                          self.pixel_pos[1] + self.image_size[1]) )

        # ((lon0, lat0), (lon1, lat1))
        self.coords = ( tileproj.pixel2lon_lat(self.corners[0], self.z),
                        tileproj.pixel2lon_lat(self.corners[1], self.z) )

        polygon_points = [ (self.coords[i][0], self.coords[j][1])
                           for i, j in ((0, 0), (1, 0), (1, 1), (0, 1), (0, 0)) ]
        coords_wkt = ", ".join([ "%s %s" % point for point in polygon_points ])
        polygon_wkt = 'POLYGON ((%s))' % coords_wkt

        self.polygon = wkt.loads(polygon_wkt)

        # times
        self.render_time = None
        self.serializing_time = None
        self.deserializing_time = 0
        self.saving_time = 0

        # Tile emulation
        self.meta_index = (0, 0)


    def __repr__(self) -> str:
        return "PixelTile(%d,%d,%d)" % (self.z, self.x, self.y)


    def child(self, tile:Tile):
        return None


    def children(self):
        return []


# TODO: MetaTile factory

# Children = List[MetaTile]
class MetaTile:
    def __init__(self, z:int, x:int, y:int, wanted_size:int, tile_size:int) -> None:
        self.z = z
        self.x = x
        self.y = y

        self.wanted_size = wanted_size  # in tiles
        self.size = min(2**z, wanted_size)
        self.tile_size = tile_size

        self.is_empty = True  # to simplify code in store_metatile()
        self.render = True  # this is going to be reset by store_metatile()

        # NOTE: children are not precomputed because it's recursive with no bounds
        # see children()
        # self._children:Optional[Children] = None
        self._children = None

        self.tiles = [ Tile(self.z, self.x + i, self.y + j, self)
                       for i in range(self.size) for j in range(self.size) ]

        self.im: Optional[bytes] = None

        # (x, y)
        self.pixel_pos = (self.x * self.tile_size, self.y * self.tile_size)
        # (w, h)
        self.image_size = (self.size * self.tile_size, self.size * self.tile_size)

        # ((x0, y0), (x1, y1))
        self.corners = ( self.pixel_pos,
                         (self.pixel_pos[0] + self.image_size[0],
                          self.pixel_pos[1] + self.image_size[1]) )

        # ((lon0, lat0), (lon1, lat1))
        self.coords = ( tileproj.pixel2lon_lat(self.corners[0], self.z),
                        tileproj.pixel2lon_lat(self.corners[1], self.z) )

        polygon_points = [ (self.coords[i][0], self.coords[j][1])
                           for i, j in ((0, 0), (1, 0), (1, 1), (0, 1), (0, 0)) ]
        coords_wkt = ", ".join([ "%s %s" % point for point in polygon_points ])
        polygon_wkt = 'POLYGON ((%s))' % coords_wkt

        self.polygon = wkt.loads(polygon_wkt)

        # times
        self.render_time:Optional[float] = None
        self.serializing_time:Optional[float] = None
        self.deserializing_time = 0
        self.saving_time = 0


    # see https://github.com/python/mypy/issues/2783#issuecomment-276596902
    # def __eq__(self, other:MetaTile) -> bool:  # type: ignore
    def __eq__(self, other) -> bool:  # type: ignore
        return ( self.z == other.z and self.x == other.x and self.y == other.y
                 and self.size == other.size )


    def __repr__(self) -> str:
        return "MetaTile(%d,%d,%d)" % (self.z, self.x, self.y)


    # def children(self) -> Children:
    def children(self):
        if self._children is None:
            if self.size == self.wanted_size:
                self._children = [ MetaTile(self.z+1,
                                            2*self.x + i*self.size,
                                            2*self.y + j*self.size,
                                            self.wanted_size, self.tile_size)
                                   for i in range(2) for j in range(2) ]
            else:
                self._children = [ MetaTile(self.z+1, 2*self.x, 2*self.y,
                                            self.wanted_size, self.tile_size) ]

        return self._children


    def __contains__(self, other:Tile) -> bool:
        if isinstance(other, Tile):
            if other.z == self.z-1:
                return ( self.x <= 2*other.x < self.x+self.size and
                         self.y <= 2*other.y < self.y+self.size )
            else:
                return ( self.x <= other.x < self.x+self.size and
                         self.y <= other.y < self.y+self.size )
        else:
            # TODO: more?
            return False


    # def child(self, tile:Tile) -> MetaTile:
    def child(self, tile:Tile):
        """Returns the child MetaTile were tile fits."""
        if tile in self:
            # there's only one
            return [ child for child in self.children() if tile in child ][0]
        else:
            raise ValueError("%r not in %r" % (tile, self))


    def __hash__(self):
        return hash((self.z, self.x, self.y, self.size))


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
    def __init__(self, sectors):
        self.maps = {}
        c = ConfigParser()
        c.read('bboxes.ini')
        self.minZoom = 0
        self.maxZoom = 0

        for sector in sectors:
            bb = bbox(c.get('bboxes', sector))
            # #4 is the max_z
            if bb[4] > self.maxZoom:
                self.maxZoom = int(bb[4])

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


def run_tests():
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
                 [ False, False, False, True,  True , True , False, False ],
                 [ False, False, False, True,  True , True , False, False ],
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
    run_tests()
