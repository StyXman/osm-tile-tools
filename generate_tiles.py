#!/usr/bin/env python3.6

from subprocess import call
import sys, os, os.path
import queue
from argparse import ArgumentParser
import time
import errno
import threading
import datetime
import errno
import multiprocessing
from random import randint, random
from os import getpid
import math
from signal import signal, SIGINT, SIG_IGN


import map_utils
# from map_utils import pyramid_count

try:
    import mapnik2 as mapnik
except:
    import mapnik

import logging
from logging import debug, info, exception
long_format = "%(asctime)s %(name)16s:%(lineno)-4d (%(funcName)-21s) %(levelname)-8s %(message)s"
short_format = "%(asctime)s %(message)s"
from typing import Optional, List, Set, Dict

try:
    NUM_CPUS = multiprocessing.cpu_count()
except NotImplementedError:
    NUM_CPUS = 1


def floor(i: int, base: int=1) -> int:
    """Round down i to the closest multiple of base."""
    return base * (i // base)


def pyramid_count(min_zoom, max_zoom):
    return sum([ 4**i for i in range(max_zoom - min_zoom + 1) ])


class RenderStack:
    """A render stack implemented with a list... and more.

    Although this is implemented with a list, I prefer the semantic of these
    methods and the str() representation given by the list being pop from/push
    into the left.

    The stack has a first element, which is the one ready to be pop()'ed.
    Because this element might need to be returned, there's the confirm()
    method which actually pops it and replaces it with the next one.

    The stack also autofills with children when we pop an element. Because
    these children might not be needed to be rendered, they're stored in
    another list, to_validate. Once we know the tile is not empty or any
    other reason to skip it, we notify() it."""
    def __init__(self, max_zoom:int, push_children:bool=True) -> None:
        # I don't need order here, it's (probably) better if I validate tiles
        # as soon as possible
        self.first:Optional[map_utils.MetaTile] = None
        self.ready:List[map_utils.Tile] = []
        self.to_validate:Set[map_utils.MetaTile] = set()
        self.max_zoom = max_zoom
        self.push_children = push_children


    def push(self, o:map_utils.MetaTile) -> None:
        self.to_validate.add(o)
        # debug("%s, %s, %s", self.first, self.ready, self.to_validate)


    def pop(self) -> map_utils.MetaTile:
        return self.first


    def confirm(self) -> None:
        """Mark the top of the stack as sent to render, factually pop()'ing it."""
        if self.first is not None:
            metatile:map_utils.MetaTile = self.first
            if metatile.z < self.max_zoom and self.push_children:
                # automatically push the children
                for child in metatile.children(): # type: map_utils.MetaTile
                    self.push(child)

        t:Optional[map_utils.Tile] = None
        if len(self.ready) > 0:
            t = self.ready.pop(0)

        self.first = t
        # debug("%s, %s, %s", self.first, self.ready, self.to_validate)


    def size(self) -> int:
        # HACK: int(bool) \belongs (0, 1)
        # debug("%s, %s, %s", self.first, self.ready, self.to_validate)
        ans:int = ( int(self.first is not None) + len(self.ready) +
                    len(self.to_validate) )
        # debug(ans)
        return ans


    def notify(self, metatile:map_utils.MetaTile, render:bool) -> None:
        """The MetaTile needs to be rendered."""
        debug("%s, %s", metatile, render)
        self.to_validate.remove(metatile)

        if render:
            if self.first is not None:
                self.ready.insert(0, self.first)

            self.first = metatile


RenderChildren = Dict[map_utils.Tile, bool]
class RenderThread:
    def __init__(self, opts, backend, queues) -> None:
        self.backend = backend
        self.queues  = queues
        self.opts = opts
        self.metatile_size:int = opts.metatile_size
        self.tile_size:int = 256
        self.image_size:int = self.tile_size * self.metatile_size

        if self.opts.parallel == 'single':
            # RenderThread.loop() is not called in single mode
            # so do this here
            self.pid = getpid()
            self.load_map()


    def render_metatile(self, metatile:map_utils.MetaTile) -> Dict[map_utils.Tile, bool]:
        z = metatile.z
        x = metatile.x
        y = metatile.y

        # TODO: move all this somewhere else
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

        debug("[%s] bailing out", self.pid)
        bail_out = True

        start = time.perf_counter()

        # handling C-c: if we're rendering, the exception won't be raised until
        # mapnik has finished, and throwing away that work would be a shame

        # so, from the docs: If an exception occurs in any of the clauses and is
        # not handled, the exception is temporarily saved. The finally clause
        # is executed. If there is a saved exception it is re-raised at the
        # end of the finally clause

        im = mapnik.Image(self.image_size, self.image_size)

        # critical section, disable signals
        if self.opts.parallel != 'single':
            sig = signal(SIGINT, SIG_IGN)

        if not self.opts.dry_run:
            # Render image with default Agg renderer
            mapnik.render(self.m, im)
            # TODO: handle exception, send back into queue
        else:
            debug('[%s] thumbtumbling', self.pid)
            time.sleep(randint(0, 30) / 10)

        debug("[%s] not bailing out", self.pid)
        bail_out = False
        mid = time.perf_counter()
        render_children = self.store_metatile(im, metatile)
        end = time.perf_counter()

        debug("<== [%s] %r: %s", self.pid, metatile, ('old', mid-start, end-mid))
        self.queues[1].put(('old', metatile, mid-start, end-mid))
        debug("<<< [%s]", self.pid)

        # end critical section, restore signal
        if self.opts.parallel != 'single':
            signal(SIGINT, sig)

        return render_children, bail_out


    def store_metatile(self, im, metatile):
        render_children:Dict[map_utils.Tile, bool] = {}

        # save the image, splitting it in the right amount of tiles
        for tile in metatile.tiles:
            self.store_tile(im, metatile, tile, render_children)

        return render_children


    def store_tile(self, im, metatile, tile, render_children):
        i, j = tile.meta_index

        if not self.opts.dry_run:
            # TODO: Tile.meta_pixel_coords
            img = im.view(i*self.tile_size, j*self.tile_size,
                            self.tile_size,   self.tile_size)
            tile.data = img.tostring('png256')
            # TODO: move to Tile
            is_empty = map_utils.is_empty(tile.data)

            if not is_empty or self.opts.empty == 'write':
                self.backend.store(tile)
            elif is_empty and self.opts.empty == 'link':
                # TODO
                pass
        else:
            is_empty = ( random() <= 0.75 and
                         not 2**metatile.z < self.opts.metatile_size )

        if ( not is_empty and not self.opts.single_tiles and
             tile.z < self.opts.max_zoom ):

            # debug( "%s; %s; %d < %d", not is_empty,
            #        not self.opts.single_tiles, tile.z, self.opts.max_zoom )

            # at least something to render
            render_children[metatile.child(tile)] = True
        # TODO: handle empty and link or write; pyramid stuff

        if not self.opts.dry_run:
            self.backend.commit()


    def load_map(self):
        start = time.perf_counter()
        self.m  = mapnik.Map(self.image_size, self.image_size)
        # Load style XML
        if not self.opts.dry_run:
            mapnik.load_map(self.m, self.opts.mapfile, True)
        end = time.perf_counter()
        debug('Map loading took %.6fs', end-start)

        # Obtain <Map> projection
        self.prj = mapnik.Projection(self.m.srs)
        # Projects between tile pixel co-ordinates and LatLong (EPSG:4326)
        self.tileproj = map_utils.GoogleProjection(opts.max_zoom+1)


    def loop(self):
        self.pid = getpid()
        self.load_map()

        debug('[%s] looping the loop', self.pid)

        finished = False
        while not finished:
            try:
                finished = self.single_step()
            except KeyboardInterrupt:
                # do nothing, we'll be outta here
                debug('break!')
                pass

        debug("[%s] I'm outta here...", self.pid)


    def single_step(self):
        # Fetch a tile from the queue and render it
        debug("[%s] >>>", self.pid)
        metatile:Optional[map_utils.MetaTile] = self.queues[0].get()
        debug("[%s] ==> %r", self.pid, metatile)
        if metatile is None:
            # self.q.task_done()
            debug('[%s] None, ending loop' % self.pid)
            return True

        # TODO: move all these checks to another thread/process.
        skip:bool
        if self.opts.skip_existing or self.opts.skip_newer is not None:
            debug('[%s] skip test existing:%s, newer:%s',
                  self.pid, self.opts.skip_existing, self.opts.skip_newer)
            skip = True

            for tile in metatile.tiles: # type: map_utils.Tile
                if self.opts.skip_existing:
                    skip = skip and self.backend.exists(tile)
                else:
                    skip= ( skip and
                            self.backend.newer_than(tile, self.opts.skip_newer,
                                                    self.opts.missing_as_new) )
        else:
            skip = False

        render_children:Dict[map_utils.Tile, bool] = {}
        if not skip:
            render_children, bail_out = self.render_metatile(metatile)
        else:
            # TODO: ugh?
            bail_out = False
            debug("[%s] not bailing out", self.pid)
            self.queues[1].put(('skept', metatile))

            # but notify the children, so they get a chance to be rendered
            if metatile.z < self.opts.max_zoom:
                for child in metatile.children():
                    # we have no other info about whether they should be
                    # rendered or not, so render them just in case. at worst,
                    # they could either be empty tiles or too new too
                    render_children[child] = True

        # debug(render_children)
        for tile, render in render_children.items():
            debug("<== [%s] %r: %s", self.pid, tile, render)
            self.queues[1].put(('new', tile, render))
            debug("<<< [%s]", self.pid)

        # self.q.task_done()
        return bail_out


class Master:
    def __init__(self, opts) -> None:
        self.opts = opts
        self.renderers = {}
        # we need at least space for the initial batch
        # but do not auto push children in tiles mode
        self.work_stack = RenderStack(opts.max_zoom, not self.opts.single_tiles)

        # counters
        self.went_out = self.came_back = 0
        self.tiles_to_render = self.tiles_rendered = self.tiles_skept = 0

        if self.opts.parallel == 'fork':
            debug('forks, using mp.Queue()')

            # work_out queue is size 1, so higher zoom level tiles don't pile up
            # there if there are lower ZL tiles ready in the work_stack.
            self.work_in = multiprocessing.Queue(5*self.opts.threads)
            self.work_out = multiprocessing.Queue(1)
        elif self.opts.parallel == 'threads':
            debug('threads, using queue.Queue()')
            # TODO: warning about mapnik and multithreads
            self.work_in = queue.Queue(32)
            self.work_out = queue.Queue(32)
        else:
            debug('single mode, using queue.Queue()')
            self.work_in = queue.Queue(5)
            self.work_out = queue.Queue(1)


    def tiles_per_metatile(self, zoom):
        return min(self.opts.metatile_size, 2**zoom) ** 2


    def progress(self, metatile, *args, format='%s'):
        percentage = ( (self.tiles_rendered + self.tiles_skept) /
                       self.tiles_to_render * 100 )

        format = "[%d+%d/%d: %7.4f%%] %r: " + format
        info(format, self.tiles_rendered, self.tiles_skept, self.tiles_to_render,
             percentage, metatile, *args)


    def render_tiles(self) -> None:
        debug("render_tiles(%s)", self.opts)

        backends:Dict[str,Any] = dict(
            tiles=  map_utils.DiskBackend,
            mbtiles=map_utils.MBTilesBackend,
            )

        backend = backends[self.opts.format](self.opts.tile_dir, self.opts.bbox)

        # Launch rendering threads
        if self.opts.parallel != 'single':
            for i in range(self.opts.threads):
                renderer = RenderThread( self.opts, backend,
                                         (self.work_out, self.work_in) )

                if self.opts.parallel == 'fork':
                    debug('mp.Process()')
                    render_thread = multiprocessing.Process(target=renderer.loop)
                elif self.opts.parallel == 'threads':
                    debug('th.Thread()')
                    render_thread = threading.Thread(target=renderer.loop)

                render_thread.start()

                if self.opts.parallel:
                    debug("Started render thread %s" % render_thread.name)
                else:
                    debug("Started render thread %s" % render_thread.getName())

                self.renderers[i] = render_thread
        else:
            self.renderer = RenderThread( self.opts, backend,
                                          (self.work_out, self.work_in) )

        if not os.path.isdir(self.opts.tile_dir):
            debug("creating dir %s", self.opts.tile_dir)
            os.makedirs(self.opts.tile_dir, exist_ok=True)

        initial_metatiles = []
        if not self.opts.single_tiles:
            debug('rendering bbox %s:%s', self.opts.bbox_name, self.opts.bbox)
            for x in range(0, 2**self.opts.min_zoom, self.opts.metatile_size):
                for y in range(0, 2**self.opts.min_zoom, self.opts.metatile_size):
                    t = map_utils.MetaTile(self.opts.min_zoom, x, y,
                                        self.opts.metatile_size)
                    if t in self.opts.bbox:
                        initial_metatiles.append(t)
        else:
            # TODO: if possible, order them in depth first/proximity? fashion.
            debug('rendering individual tiles')
            for i in self.opts.tiles:
                z, x, y = map(int, i.split(','))
                t = map_utils.MetaTile(z, x, y, self.opts.metatile_size)
                initial_metatiles.append(t)

        try:
            self.loop(initial_metatiles)
        except KeyboardInterrupt as e:
            debug(e)
            raise SystemExit("Ctrl-c detected, exiting...")
        finally:
            self.finish()


    def loop(self, initial_metatiles) -> None:
        for metatile in initial_metatiles:
            debug("... %r" % (metatile, ))
            self.work_stack.push(metatile)
            # make sure they're rendered!
            self.work_stack.notify(metatile, True)

            if self.opts.single_tiles:
                self.tiles_to_render += len(metatile.tiles)
                # debug("%r: %d", metatile, tiles_to_render)

        if not self.opts.single_tiles:
            # all initial_metatiles are from the same zoom level
            first_tiles = len(initial_metatiles)
            self.tiles_to_render = ( first_tiles * len(initial_metatiles[0].tiles) *
                                     pyramid_count(opts.min_zoom, opts.max_zoom) )

        # I could get to the pipes used for the Queues, but it's useless, as
        # they're constantly ready. keep the probing version, so select()ing on
        # them leads to a tight loop
        while self.work_stack.size() > 0 or self.went_out > self.came_back:
            # debug("ws.size(): %s; wo > cb: %d > %d", self.work_stack.size(),
            #       went_out, came_back)

            # the doc says this is unrealiable, but we don't care
            # full() can be inconsistent only if when we test is false
            # and when we put() is true, but only the master is writing
            # so this cannot happen
            while not self.work_out.full():
                # pop from there,
                new_work = self.work_stack.pop()  # map_utils.MetaTile
                if new_work is not None:
                    # push in the writer
                    self.work_out.put(new_work, True, .1)  # 1/10s timeout
                    self.work_stack.confirm()
                    self.went_out += 1
                    debug("--> %r" % (new_work, ))

                    if self.opts.parallel == 'single':
                        self.renderer.single_step()
                        # also, get out of this place, so we can clean up
                        # in the next loop
                        break
                else:
                    # no more work to do
                    break

            # pop from the reader,
            while not self.work_in.empty():
                # 1/10s timeout
                type, *data = self.work_in.get(True, .1)  # type: str, Any
                debug("<-- %s: %r" % (type, data))

                self.handle_new_work(type, data)

        debug('out!')


    def handle_new_work(self, type, data):
        if type == 'new':
            metatile, render = data
            if metatile in self.opts.bbox:
                # MetaTile(18, 152912, 93352, 8): too new, skipping
                self.work_stack.notify(metatile, render)
                if not render:
                    self.tiles_skept += len(metatile.tiles)
            else:
                # do not render tiles out of the bbox
                debug("out of bbox, out of mind")
                self.work_stack.notify(metatile, False)
                # we count this one and all it descendents as rendered
                self.tiles_skept += ( len(metatile.tiles) *
                                      pyramid_count(metatile.z, opts.max_zoom) )

                self.progress(metatile, "out of bbox")

        elif type == 'old':
            metatile, render_time, saving_time = data
            self.tiles_rendered += len(metatile.tiles)
            self.came_back += 1

            self.progress(metatile, render_time, saving_time,
                          format="%8.3f, %8.3f")

        elif type == 'skept':
            metatile, = data
            self.tiles_skept += len(metatile.tiles)
            self.came_back += 1

            if self.opts.skip_existing:
                message = "present, skipping"
            else:
                message = "too new, skipping"

            self.progress(metatile, message)


    def finish(self):
        if self.opts.parallel != 'single':
            debug('finishing threads/procs')
            # Signal render threads to exit by sending empty request to queue
            for i in range(self.opts.threads):
                debug("--> None")
                self.work_out.put(None)

            while self.went_out > self.came_back:
                debug("%d <-> %d", self.went_out, self.came_back)
                type, *data = self.work_in.get(True)  # type: str, Any
                debug("<-- %s: %r" % (type, data))

                self.handle_new_work(type, data)

            # wait for pending rendering jobs to complete
            if not self.opts.parallel == 'fork':
                self.work_out.join()
            else:
                self.work_out.close()
                self.work_out.join_thread()

            for i in range(self.opts.threads):
                self.renderers[i].join()


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('-b', '--bbox',          dest='bbox',      default=[-180, -85, 180, 85])
    parser.add_argument('-B', '--bbox-name',     dest='bbox_name', default=None)
    parser.add_argument('-n', '--min-zoom',      dest='min_zoom',  default=0, type=int)
    parser.add_argument('-x', '--max-zoom',      dest='max_zoom',  default=18, type=int)

    parser.add_argument(      '--tiles',         dest='tiles',     default= None, nargs='+', metavar='Z,X,Y')

    parser.add_argument('-i', '--input-file',    dest='mapfile',   default='osm.xml')
    parser.add_argument('-f', '--format',        dest='format',    default='tiles') # also 'mbtiles'
    parser.add_argument('-o', '--output-dir',    dest='tile_dir',  default='tiles/')

    # TODO: check it's a power of 2
    parser.add_argument('-m', '--metatile-size', dest='metatile_size', default=1, type=int)

    parser.add_argument('-t', '--threads',       dest='threads',   default=NUM_CPUS, type=int)
    parser.add_argument('-p', '--parallel-method', dest='parallel', default='fork', choices=('threads', 'fork', 'single'))

    parser.add_argument('-X', '--skip-existing', dest='skip_existing', default=False, action='store_true')
    parser.add_argument('-N', '--skip-newer',    dest='skip_newer', default=None, type=int, metavar='DAYS')
    # parser.add_argument('-L', '--skip-symlinks', dest='skip_', default=None, type=int)
    parser.add_argument(      '--missing-as-new',  dest='missing_as_new', default=False, action='store_true',
                        help="missing tiles in a meta tile count as newer, so we don't re-render metatils with empty tiles.")
    parser.add_argument('-E', '--empty',         dest='empty',     default='skip', choices=('skip', 'link', 'write'))

    parser.add_argument('-d', '--debug',         dest='debug',     default=False, action='store_true')
    parser.add_argument(      '--dry-run',       dest='dry_run',   default=False, action='store_true')
    parser.add_argument('-l', '--log-file',      dest='log_file',  default=None)
    # TODO: buffer size (256?)
    opts = parser.parse_args()

    if opts.debug:
        logging.basicConfig(level=logging.DEBUG, format=long_format)
    else:
        logging.basicConfig(level=logging.INFO, format=short_format)

    if opts.format == 'tiles' and opts.tile_dir[-1]!='/':
        # we need the trailing /, it's actually a series of BUG s in render_tiles()
        opts.tile_dir += '/'

    opts.tile_dir = os.path.abspath(opts.tile_dir)
    if opts.skip_newer is not None:
        opts.skip_newer = datetime.datetime.now()-datetime.timedelta(days=opts.skip_newer)

    # so we find any relative resources
    opts.mapfile = os.path.basename(opts.mapfile)

    # pick bbox from bboxes.ini
    if opts.bbox_name is not None:
        a = map_utils.Atlas([ opts.bbox_name ])
        opts.bbox = map_utils.BBox(a.maps[opts.bbox_name].bbox, opts.max_zoom)
    else:
        opts.bbox = map_utils.BBox(opts.bbox, opts.max_zoom)

    # semantic opts
    opts.single_tiles = opts.tiles is not None

    return opts


if __name__  ==  "__main__":
    opts = parse_args()

    master = Master(opts)
    master.render_tiles()
