#!/usr/bin/env python

from math import pi,cos,sin,log,exp,atan
from subprocess import call
import sys, os, os.path
from Queue import Queue
from optparse import OptionParser
import time
import errno
import threading
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import sqlalchemy.exc

try:
    import mapnik2 as mapnik
except:
    import mapnik

import multiprocessing

DEG_TO_RAD = pi/180
RAD_TO_DEG = 180/pi

try:
    NUM_CPUS= multiprocessing.cpu_count ()
except NotImplementedError:
    NUM_CPUS= 1


def makedirs (_dirname):
    """ Better replacement for os.makedirs():
        doesn't fails if some intermediate dir already exists.
    """
    dirs= _dirname.split ('/')
    i= ''
    while len (dirs):
        i+= dirs.pop (0)+'/'
        try:
            os.mkdir (i)
        except OSError, e:
            if e.args[0]!=errno.EEXIST:
                raise e


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


class DiskBackend:
    def __init__ (self, base, *more):
        self.base_dir= base

    def tile_uri (self, z, x, y):
        return os.path.join (self.base_dir, str (z), str (x), str (y)+'.png')

    def store (self, z, x, y, img):
        tile_uri= self.tile_uri (z, x, y)
        makedirs (os.path.dirname (tile_uri))
        img.save (tile_uri, 'png256')

    def exists (self, z, x, y):
        tile_uri= self.tile_uri (z, x, y)
        return os.path.isfile (tile_uri)

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
        self.eng= sqlalchemy.create_engine ("sqlite:///%s.mbt" % base)
        Master.metadata.create_all (self.eng)
        Session.configure (bind=self.eng)
        self.session= Session ()

        # generate metadata
        try:
            name= KeyValue (name='name', value='perrito')
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
            version= KeyValue (name='version', value='0.1')
            self.session.add (version)
            self.session.commit ()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback ()
        try:
            description= KeyValue (name='description', value='A tileset for a friend')
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

    def store (self, z, x, y, img):
        t= Tile (zoom_level=z, tile_column=x, tile_row=y, tile_data=img.tostring ('png256'))
        self.session.add (t)

    def commit (self):
        if len (self.session.dirty)>0:
            self.session.commit ()

    def exists (self, z, x, y):
        return self.session.query (sqlalchemy.func.count (Tile.zoom_level)).\
                            filter (Tile.zoom_level==z).\
                            filter (Tile.tile_column==x).\
                            filter (Tile.tile_row==y)[0][0]==1 # 1st col, 1st row

class RenderThread:
    def __init__(self, opts, backend, queue):
        self.backend= backend
        self.q = queue
        self.skip_existing= opts.skip
        self.meta_size= opts.meta_size
        self.tile_size= 256
        self.image_size= self.tile_size*self.meta_size
        self.m = mapnik.Map (self.image_size, self.image_size)
        # self.printLock = printLock
        # Load style XML
        mapnik.load_map (self.m, opts.mapfile, True)
        # Obtain <Map> projection
        self.prj= mapnik.Projection (self.m.srs)
        # Projects between tile pixel co-ordinates and LatLong (EPSG:4326)
        self.tileproj= GoogleProjection (opts.max_zoom+1)

    def render_tile (self, x, y, z):
        # Calculate pixel positions of bottom-left & top-right
        p0= (x * self.tile_size, (y + self.meta_size) * self.tile_size)
        p1= ((x + self.meta_size) * self.tile_size, y * self.tile_size)

        # Convert to LatLong (EPSG:4326)
        l0= self.tileproj.fromPixelToLL (p0, z);
        l1= self.tileproj.fromPixelToLL (p1, z);

        # Convert to map projection (e.g. mercator co-ords EPSG:900913)
        c0= self.prj.forward(mapnik.Coord (l0[0], l0[1]))
        c1= self.prj.forward(mapnik.Coord (l1[0], l1[1]))

        # Bounding box for the tile
        if hasattr (mapnik, 'mapnik_version') and mapnik.mapnik_version () >= 800:
            bbox= mapnik.Box2d(c0.x, c0.y, c1.x, c1.y)
        else:
            bbox= mapnik.Envelope(c0.x, c0.y, c1.x, c1.y)

        self.m.resize (self.image_size, self.image_size)
        self.m.zoom_to_box (bbox)
        if self.m.buffer_size < 128:
            self.m.buffer_size= 128

        # Render image with default Agg renderer
        start= time.time ()
        im = mapnik.Image (self.image_size, self.image_size)
        mapnik.render (self.m, im)
        end= time.time ()

        # save the image, splitting it in the right amount of tiles
        # we use min() so we can support low zoom levels with less than meta_size tiles
        for i in xrange (min (self.meta_size, 2**z)):
            for j in xrange (min (self.meta_size, 2**z)):
                img= im.view (i*self.tile_size, j*self.tile_size, self.tile_size, self.tile_size)
                self.backend.store (z, x+i, y+j, img)

            self.backend.commit ()

        # self.printLock.acquire()
        print "%d:%d:%d: %f" % (x, y, z, end-start)
        # self.printLock.release()

    def loop (self):
        while True:
            # Fetch a tile from the queue and render it
            r= self.q.get ()
            if r is None:
                self.q.task_done ()
                break
            else:
                (x, y, z)= r

            if self.skip_existing:
                skip= True
                # we use min() so we can support low zoom levels with less than meta_size tiles
                for tile_x in range (x, x+min (self.meta_size, 2**z)):
                    for tile_y in range (y, y+min (self.meta_size, 2**z)):
                        skip= skip and self.backend.exists (z, tile_x, tile_y)
                        # print "%s: %s" % (tile_uri, all_exist)
            else:
                skip= False

            if not skip:
                self.render_tile (x, y, z)

            # bytes= os.stat (tile_uri)[6]
            # empty= ''
            # if bytes==103:
            #     empty = " Empty Tile "
            # print name, ":", z, x, y, exists, empty
            self.q.task_done ()


def render_tiles(opts):
    print "render_tiles(",opts,")"

    backends= dict (
        tiles=   DiskBackend,
        mbtiles= MBTilesBackend,
        )

    try:
        backend= backends[opts.format](opts.tile_dir, opts.bbox)
    except KeyError:
        raise

    # Launch rendering threads
    queue= Queue (32)
    renderers= {}
    for i in range (opts.threads):
        renderer= RenderThread (opts, backend, queue)
        render_thread= threading.Thread (target=renderer.loop)
        render_thread.start ()
        #print "Started render thread %s" % render_thread.getName()
        renderers[i]= render_thread

    if not os.path.isdir (opts.tile_dir):
         os.mkdir (opts.tile_dir)

    gprj= GoogleProjection (opts.max_zoom+1)

    ll0= (bbox[0], bbox[3])
    ll1= (bbox[2], bbox[1])

    image_size= 256.0*opts.meta_size

    for z in range (opts.min_zoom, opts.max_zoom + 1):
        px0= gprj.fromLLtoPixel (ll0, z)
        px1= gprj.fromLLtoPixel (ll1, z)

        for x in range (int (px0[0]/image_size), int (px1[0]/image_size)+1):
            # Validate x co-ordinate
            if (x < 0) or (x*opts.meta_size >= 2**z):
                continue

            for y in range (int (px0[1]/image_size), int (px1[1]/image_size)+1):
                # Validate x co-ordinate
                if (y < 0) or (y*opts.meta_size >= 2**z):
                    continue

                # Submit tile to be rendered into the queue
                t= (x*opts.meta_size, y*opts.meta_size, z)
                try:
                    queue.put (t)
                except KeyboardInterrupt:
                    raise SystemExit("Ctrl-c detected, exiting...")

    # Signal render threads to exit by sending empty request to queue
    for i in range (opts.threads):
        queue.put (None)
    # wait for pending rendering jobs to complete
    queue.join ()
    for i in range (opts.threads):
        renderers[i].join ()

if __name__ == "__main__":
    parser= OptionParser ()
    parser.add_option ('-b', '--bbox',          dest='bbox',      default='-180,-85,180,85')
    parser.add_option ('-f', '--format',        dest='format',    default='tiles') # also 'mbtiles'
    parser.add_option ('-i', '--input-file',    dest='mapfile',   default='osm.xml')
    parser.add_option ('-m', '--metatile-size', dest='meta_size', default=1, type='int')
    parser.add_option ('-n', '--min-zoom',      dest='min_zoom',  default=0, type="int")
    parser.add_option ('-o', '--output-dir',    dest='tile_dir',  default='tiles/')
    parser.add_option ('-s', '--skip-existing', dest='skip',      default=False, action='store_true')
    parser.add_option ('-t', '--threads',       dest='threads',   default=NUM_CPUS, type="int")
    parser.add_option ('-x', '--max-zoom',      dest='max_zoom',  default=18, type="int")
    opts, args= parser.parse_args ()

    if opts.format=='tiles' and opts.tile_dir[-1]!='/':
        # we need the trailing /, it's actually a series of BUG s in render_tiles()
        opts.tile_dir+= '/'

    bbox = [ float (x) for x in opts.bbox.split (',') ]

    opts.tile_dir= os.path.abspath (opts.tile_dir)

    # so we find any relative resources
    os.chdir (os.path.dirname (opts.mapfile))
    opts.mapfile= os.path.basename (opts.mapfile)

    render_tiles(opts)
