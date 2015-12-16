#!/usr/bin/env python

from subprocess import call
import sys, os, os.path
from Queue import Queue
from argparse import ArgumentParser
import time
import errno
import threading
import datetime
import errno

import map_utils

try:
    import mapnik2 as mapnik
except:
    import mapnik

import multiprocessing

try:
    NUM_CPUS= multiprocessing.cpu_count ()
except NotImplementedError:
    NUM_CPUS= 1

class RenderThread:
    def __init__(self, opts, backend, queue):
        self.backend= backend
        self.q = queue
        self.opts= opts
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
        self.tileproj= map_utils.GoogleProjection (opts.max_zoom+1)

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
        try:
            mapnik.render (self.m, im)
        except RuntimeError as e:
            print "%d:%d:%d: %s" % (x, y, z, e)
        else:
            end= time.time ()

            # save the image, splitting it in the right amount of tiles
            # we use min() so we can support low zoom levels with less than meta_size tiles
            for i in xrange (min (self.meta_size, 2**z)):
                for j in xrange (min (self.meta_size, 2**z)):
                    img= im.view (i*self.tile_size, j*self.tile_size, self.tile_size, self.tile_size)
                    data= img.tostring ('png256')
                    if not map_utils.is_empty (data):
                        self.backend.store (z, x+i, y+j, data)
                    else:
                        if self.opts.empty=='skip':
                            # empty tile, skip
                            print "%d:%d:%d: empty" % (z, x+i, y+j)
                            continue

                self.backend.commit ()

            print "%d:%d:%d: %f" % (x, y, z, end-start)

    def loop (self):
        while True:
            # Fetch a tile from the queue and render it
            r= self.q.get ()
            if r is None:
                self.q.task_done ()
                break
            else:
                (x, y, z)= r

            if self.opts.skip_existing or self.opts.skip_newer is not None:
                skip= True
                # we use min() so we can support low zoom levels with less than meta_size tiles
                for tile_x in range (x, x+min (self.meta_size, 2**z)):
                    for tile_y in range (y, y+min (self.meta_size, 2**z)):
                        if self.opts.skip_existing:
                            skip= skip and self.backend.exists (z, tile_x, tile_y)
                        else:
                            skip= (skip and
                                self.backend.newer_than (z, tile_x, tile_y,
                                                         self.opts.skip_newer))
            else:
                skip= False

            if not skip:
                self.render_tile (x, y, z)
            else:
                if self.skip_existing:
                    print "%d:%d:%d: present, skipping" % (x, y, z)
                else:
                    print "%d:%d:%d: too new, skipping" % (x, y, z)

            self.q.task_done ()


def render_tiles(opts):
    print "render_tiles(",opts,")"

    backends= dict (
        tiles=   map_utils.DiskBackend,
        mbtiles= map_utils.MBTilesBackend,
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

    if opts.tiles is None:
        render_bbox (opts, queue, renderers)
    else:
        for i in opts.tiles:
            z, x, y= map (int, i.split (','))
            queue.put ((x, y, z))

    finish (queue, renderers)

def render_bbox (opts, queue, renderers):
    gprj= map_utils.GoogleProjection (opts.max_zoom+1)

    bbox = opts.bbox
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

def finish (queue, renderers):
    # Signal render threads to exit by sending empty request to queue
    for i in range (opts.threads):
        queue.put (None)

    # wait for pending rendering jobs to complete
    queue.join ()
    for i in range (opts.threads):
        renderers[i].join ()

if __name__ == "__main__":
    parser= ArgumentParser ()

    # g1= parser.add_mutually_exclusive_group ()
    # g2= g1.add_argument_group ()
    parser.add_argument ('-b', '--bbox',          dest='bbox',      default=[-180, -85, 180, 85], type=map_utils.bbox)
    parser.add_argument ('-B', '--bbox-name',     dest='bbox_name', default=None)
    parser.add_argument ('-n', '--min-zoom',      dest='min_zoom',  default=0, type=int)
    parser.add_argument ('-x', '--max-zoom',      dest='max_zoom',  default=18, type=int)

    parser.add_argument (      '--tile',          dest='tiles',     default= None, nargs='*', metavar='Z,X,Y')

    parser.add_argument ('-i', '--input-file',    dest='mapfile',   default='osm.xml')
    parser.add_argument ('-f', '--format',        dest='format',    default='tiles') # also 'mbtiles'
    parser.add_argument ('-o', '--output-dir',    dest='tile_dir',  default='tiles/')

    parser.add_argument ('-m', '--metatile-size', dest='meta_size', default=1, type=int)
    parser.add_argument ('-t', '--threads',       dest='threads',   default=NUM_CPUS, type=int)

    parser.add_argument ('-X', '--skip-existing', dest='skip_existing', default=False, action='store_true')
    parser.add_argument ('-N', '--skip-newer',    dest='skip_newer', default=None, type=int)
    # parser.add_argument ('-L', '--skip-symlinks', dest='skip_', default=None, type=int)
    parser.add_argument ('-E', '--empty',         dest='empty',     default='skip', choices=('skip', 'link', 'render'))
    opts= parser.parse_args ()

    if opts.format=='tiles' and opts.tile_dir[-1]!='/':
        # we need the trailing /, it's actually a series of BUG s in render_tiles()
        opts.tile_dir+= '/'

    opts.tile_dir= os.path.abspath (opts.tile_dir)
    if opts.skip_newer is not None:
        opts.skip_newer= datetime.datetime.now ()-datetime.timedelta (days=opts.skip_newer)

    # so we find any relative resources
    # os.chdir (os.path.dirname (opts.mapfile))
    opts.mapfile= os.path.basename (opts.mapfile)

    # pick bbox from bboxes.ini
    if opts.bbox_name is not None:
        a= map_utils.Atlas ([ opts.bbox_name ])
        opts.bbox= a.maps[opts.bbox_name].bbox

    render_tiles(opts)
