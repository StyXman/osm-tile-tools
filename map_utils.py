from math import pi,cos,sin,log,exp,atan
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import sqlalchemy.exc
from ConfigParser import ConfigParser
import os.path
from os.path import dirname, basename, join as path_join
from os import listdir, stat, unlink, mkdir, walk
from errno import ENOENT, EEXIST
from shutil import copy, rmtree

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

def makedirs(_dirname):
    """ Better replacement for os.makedirs():
        doesn't fails if some intermediate dir already exists.
    """
    dirs = _dirname.split('/')
    i = ''
    while len(dirs):
        i += dirs.pop(0)+'/'
        try:
            mkdir(i)
        except OSError, e:
            if e.args[0]!=EEXIST:
                raise e
