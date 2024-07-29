from math import pi, cos, sin, log, exp, atan
from typing import List, Tuple, Dict, Optional, Any, Union

from shapely.geometry import Polygon


# DEG_TO_RAD:float = pi / 180
# RAD_TO_DEG:float = 180 / pi
DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi


class GoogleProjection:
    """
    This class converts from LonLat to pixel and vice versa. For that, it pre
    calculates some values for each zoom level, which are store in 3 arrays.

    For information about the formulas in lon_lat2pixel() and pixel2lon_lat(), see
    https://en.wikipedia.org/wiki/Mercator_projection#Mathematics_of_the_Mercator_projection
    """

    # see also https://alastaira.wordpress.com/2011/01/23/the-google-maps-bing-maps-spherical-mercator-projection/

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
            # the world doubles in size on each zoom level
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


    def __iter__(self):
        return self.iter()


    def iter(self):
        """Returns a generator over the 'coords'."""
        yield self.z
        yield self.x
        yield self.y


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

        self.polygon = Polygon(polygon_points)

        # times
        self.render_time = 0
        self.serializing_time = 0
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


    # TODO: move to BaseTile
    def __iter__(self):
        return self.iter()


    def iter(self):
        """Returns a generator over the 'coords'."""
        yield self.z
        yield self.x
        yield self.y


    def times(self):
        return (self.render_time, self.serializing_time, self.deserializing_time,
                self.saving_time)

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

        self.polygon = Polygon(polygon_points)

        # times
        self.render_time:float = 0
        self.serializing_time:float = 0
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
                self._children = [ MetaTile(self.z + 1,
                                            2 * self.x + i * self.size,
                                            2 * self.y + j * self.size,
                                            self.wanted_size, self.tile_size)
                                   for i in range(2) for j in range(2) ]
            else:
                self._children = [ MetaTile(self.z + 1, 2 * self.x, 2 * self.y,
                                            self.wanted_size, self.tile_size) ]
            debug((self, self._children))

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


    def times(self):
        return (self.render_time, self.serializing_time, self.deserializing_time,
                self.saving_time)
