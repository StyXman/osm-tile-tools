#!/usr/bin/env python3

from subprocess import call
import sys, os, os.path
from queue import Queue
from argparse import ArgumentParser
import time
import errno
import threading
import datetime
import errno
import multiprocessing

import map_utils

try:
    import mapnik2 as mapnik
except:
    import mapnik

import logging
from logging import debug

try:
    NUM_CPUS = multiprocessing.cpu_count()
except NotImplementedError:
    NUM_CPUS = 1


class RenderThread:
    def __init__(self, opts, backend, queues):
        self.backend = backend
        self.queues  = queues
        self.opts = opts
        self.metatile_size = opts.metatile_size
        self.tile_size = 256
        self.image_size = self.tile_size*self.metatile_size
        start = time.perf_counter()
        self.m  = mapnik.Map(self.image_size, self.image_size)
        # self.printLock  = printLock
        # Load style XML
        mapnik.load_map(self.m, opts.mapfile, True)
        end = time.perf_counter()
        debug('Map loading took %.6fs', end-start)
        # Obtain <Map> projection
        self.prj = mapnik.Projection(self.m.srs)
        # Projects between tile pixel co-ordinates and LatLong (EPSG:4326)
        self.tileproj = map_utils.GoogleProjection(opts.max_zoom+1)


    def render_tile(self, x, y, z):
        # Calculate pixel positions of bottom-left & top-right
        p0 = (x * self.tile_size, (y + self.metatile_size) * self.tile_size)
        p1 = ((x + self.metatile_size) * self.tile_size, y * self.tile_size)

        # Convert to LatLong (EPSG:4326)
        l0 = self.tileproj.fromPixelToLL(p0, z);
        l1 = self.tileproj.fromPixelToLL(p1, z);

        # Convert to map projection (e.g. mercator co-ords EPSG:900913)
        c0 = self.prj.forward(mapnik.Coord(l0[0], l0[1]))
        c1 = self.prj.forward(mapnik.Coord(l1[0], l1[1]))

        # Bounding box for the tile
        if hasattr(mapnik, 'mapnik_version') and mapnik.mapnik_version() >= 800:
            bbox = mapnik.Box2d(c0.x, c0.y, c1.x, c1.y)
        else:
            bbox = mapnik.Envelope(c0.x, c0.y, c1.x, c1.y)

        self.m.resize(self.image_size, self.image_size)
        self.m.zoom_to_box(bbox)
        if self.m.buffer_size < 128:
            self.m.buffer_size = 128

        # Render image with default Agg renderer
        start = time.perf_counter()
        im = mapnik.Image(self.image_size, self.image_size)
        try:
            mapnik.render(self.m, im)
        except RuntimeError as e:
            print("%d:%d:%d: %s" % (z, x, y, e), file=sys.stderr)
            sys.stderr.flush()
        else:
            mid= time.perf_counter()

            # save the image, splitting it in the right amount of tiles
            # we use min() so we can support low zoom levels with less than metatile_size tiles
            for i in range(min(self.metatile_size, 2**z)):
                for j in range(min(self.metatile_size, 2**z)):
                    img = im.view(i*self.tile_size, j*self.tile_size, self.tile_size, self.tile_size)
                    data = img.tostring('png256')
                    if not map_utils.is_empty(data):
                        self.backend.store(z, x+i, y+j, data)
                    else:
                        if self.opts.empty == 'skip':
                            # empty tile, skip
                            print("%d:%d:%d: empty" % (z, x+i, y+j))
                            continue

                self.backend.commit()

            end = time.perf_counter()
            print("%d:%d:%d: %f, %f" % (z, x, y, mid-start, end-mid))
            sys.stdout.flush()


    def loop(self):
        debug('%s looping the loop', self)
        while True:
            # Fetch a tile from the queue and render it
            r = self.queues[0].get()
            if r is None:
                # self.q.task_done()
                debug('ending loop')
                break
            else:
                (x, y, z) = r

            if self.opts.skip_existing or self.opts.skip_newer is not None:
                debug('skip test existing:%s, newer:%s',
                       self.opts.skip_existing, self.opts.skip_newer)
                skip= True
                # we use min() so we can support low zoom levels with less than metatile_size tiles
                for tile_x in range(x, x+min(self.metatile_size, 2**z)):
                    for tile_y in range(y, y+min(self.metatile_size, 2**z)):
                        if self.opts.skip_existing:
                            skip= skip and self.backend.exists(z, tile_x, tile_y)
                        else:
                            skip=(skip and
                                self.backend.newer_than(z, tile_x, tile_y,
                                                         self.opts.skip_newer))
            else:
                skip= False

            if not skip:
                self.render_tile(x, y, z)
            else:
                if self.opts.skip_existing:
                    print("%d:%d:%d: present, skipping" % (x, y, z))
                else:
                    print("%d:%d:%d: too new, skipping" % (x, y, z))

            # self.q.task_done()


def render_tiles(opts):
    debug("render_tiles(%s)", opts)

    backends = dict(
        tiles=  map_utils.DiskBackend,
        mbtiles=map_utils.MBTilesBackend,
        )

    try:
        backend = backends[opts.format](opts.tile_dir, opts.bbox)
    except KeyError:
        raise

    # Launch rendering threads
    if opts.parallel == 'fork':
        debug('forks, using mp.Queue()')
        queues = (multiprocessing.Queue(opts.threads+1),
                  multiprocessing.Queue(4*opts.threads+1))
    else:
        debug('threads or single, using queue.Queue()')
        # TODO: this and the warning about mapnik and multithreads
        queues = (Queue(32), None)

    renderers = {}

    for i in range(opts.threads):
        renderer = RenderThread(opts, backend, queues)

        if opts.parallel!='single':
            if opts.parallel == 'fork':
                debug('mp.Process()')
                render_thread = multiprocessing.Process(target=renderer.loop)
            elif opts.parallel == 'threads':
                debug('th.Thread()')
                render_thread = threading.Thread(target=renderer.loop)

            render_thread.start()

            if opts.parallel:
                debug("Started render thread %s" % render_thread.name)
            else:
                debug("Started render thread %s" % render_thread.getName())

            renderers[i] = render_thread

    if not os.path.isdir(opts.tile_dir):
        debug("creating dir %s", opts.tile_dir)
        os.makedirs(opts.tile_dir, exist_ok=True)

    if opts.tiles is None:
        debug('rendering bbox %s:%s', opts.bbox_name, opts.bbox)
        render_bbox(opts, queues, renderers)
    else:
        debug('rendering individual tiles')
        for i in opts.tiles:
            z, x, y = map(int, i.split(','))
            queues[0].put((x, y, z))

    if opts.parallel == 'single':
        queues[0].put(None)
        renderer.loop()

    finish(opts, queues, renderers)


def render_bbox(opts, queues, renderers):
    gprj = map_utils.GoogleProjection(opts.max_zoom+1)

    bbox  = opts.bbox
    ll0=(bbox[0], bbox[3])
    ll1=(bbox[2], bbox[1])

    image_size = 256.0*opts.metatile_size


    for z in range(opts.min_zoom, opts.max_zoom + 1):
        px0 = gprj.fromLLtoPixel(ll0, z)
        px1 = gprj.fromLLtoPixel(ll1, z)

        for x in range(int(px0[0]/image_size), int(px1[0]/image_size)+1):
            # Validate x co-ordinate
            if (x < 0) or (x*opts.metatile_size >= 2**z):
                continue

            for y in range(int(px0[1]/image_size), int(px1[1]/image_size)+1):
                # Validate x co-ordinate
                if (y < 0) or (y*opts.metatile_size >= 2**z):
                    continue

                # Submit tile to be rendered into the queue
                t = (x*opts.metatile_size, y*opts.metatile_size, z)
                try:
                    queues[0].put(t)
                except KeyboardInterrupt:
                    finish(opts, queues, renderers)
                    raise SystemExit("Ctrl-c detected, exiting...")


def finish(opts, queues, renderers):
    if opts.parallel!='single':
        debug('finishing threads/procs')
        # Signal render threads to exit by sending empty request to queue
        for i in range(opts.threads):
            queues[0].put(None)

        # wait for pending rendering jobs to complete
        if not opts.parallel == 'fork':
            queues[0].join()
        else:
            queues[0].close()
            queues[0].join_thread()

        for i in range(opts.threads):
            renderers[i].join()


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('-b', '--bbox',          dest='bbox',      default=[-180, -85, 180, 85], type=map_utils.bbox)
    parser.add_argument('-B', '--bbox-name',     dest='bbox_name', default=None)
    parser.add_argument('-n', '--min-zoom',      dest='min_zoom',  default=0, type=int)
    parser.add_argument('-x', '--max-zoom',      dest='max_zoom',  default=18, type=int)

    parser.add_argument(      '--tiles',         dest='tiles',     default= None, nargs='+', metavar='Z,X,Y')

    parser.add_argument('-i', '--input-file',    dest='mapfile',   default='osm.xml')
    parser.add_argument('-f', '--format',        dest='format',    default='tiles') # also 'mbtiles'
    parser.add_argument('-o', '--output-dir',    dest='tile_dir',  default='tiles/')

    parser.add_argument('-m', '--metatile-size', dest='metatile_size', default=1, type=int)

    parser.add_argument('-t', '--threads',       dest='threads',   default=NUM_CPUS, type=int)
    parser.add_argument('-p', '--parallel-method', dest='parallel', default='fork', choices=('threads', 'fork', 'single'))

    parser.add_argument('-X', '--skip-existing', dest='skip_existing', default=False, action='store_true')
    parser.add_argument('-N', '--skip-newer',    dest='skip_newer', default=None, type=int, metavar='DAYS')
    # parser.add_argument('-L', '--skip-symlinks', dest='skip_', default=None, type=int)
    parser.add_argument('-E', '--empty',         dest='empty',     default='skip', choices=('skip', 'link', 'render'))

    parser.add_argument('-d', '--debug',         dest='debug',     default=False, action='store_true')
    opts = parser.parse_args()

    if opts.debug:
        logging.basicConfig(level=logging.DEBUG)

    if opts.format == 'tiles' and opts.tile_dir[-1]!='/':
        # we need the trailing /, it's actually a series of BUG s in render_tiles()
        opts.tile_dir += '/'

    opts.tile_dir = os.path.abspath(opts.tile_dir)
    if opts.skip_newer is not None:
        opts.skip_newer = datetime.datetime.now()-datetime.timedelta(days=opts.skip_newer)

    # so we find any relative resources
    # os.chdir(os.path.dirname(opts.mapfile))
    opts.mapfile = os.path.basename(opts.mapfile)

    # pick bbox from bboxes.ini
    if opts.bbox_name is not None:
        a = map_utils.Atlas([ opts.bbox_name ])
        opts.bbox = a.maps[opts.bbox_name].bbox

    if opts.parallel == 'single':
        opts.threads = 1

    return opts


if __name__  ==  "__main__":
    opts = parse_args()
    render_tiles(opts)
