#!/usr/bin/env python3.6

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
import queue
from random import randint, random
from os import getpid
import math

import map_utils

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


def pyramid_tile_count(min_zoom, max_zoom):
    return sum([ 4**i for i in range(max_zoom - min_zoom + 1) ])


class RenderStack:
    """A render stack implemented with a list.

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
        debug("%s, %s, %s", self.first, self.ready, self.to_validate)


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
        debug("%s, %s, %s", self.first, self.ready, self.to_validate)


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
        self.image_size:int = self.tile_size*self.metatile_size


    # TODO: generate_tiles.py:119: error: Invalid type "generate_tiles.RenderChildren"
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

        # we must decide wether to render the subtiles/children of this tile
        render_children:Dict[map_utils.Tile, bool] = {}

        if not self.opts.dry_run:
            # Render image with default Agg renderer
            start = time.perf_counter()
            im = mapnik.Image(self.image_size, self.image_size)

            try:
                mapnik.render(self.m, im)
            except RuntimeError as e:
                exception("%r: %s", metatile, e)
            else:
                mid = time.perf_counter()

                # save the image, splitting it in the right amount of tiles
                for tile in metatile.tiles:
                    i, j = tile.meta_index

                    # TODO: Tile.meta_pixel_coords
                    img = im.view(i*self.tile_size, j*self.tile_size,
                                  self.tile_size, self.tile_size)
                    tile.data = img.tostring('png256')
                    # TODO: move to Tile
                    is_empty = map_utils.is_empty(tile.data)

                    if self.opts.tiles is not None or tile.z == self.opts.max_zoom:
                        # no children to render
                        debug("%r: no children", tile)
                        pass
                    elif not is_empty or self.opts.empty == 'write':
                        self.backend.store(tile)

                        # at least something to render
                        render_children[metatile.child(tile)] = True
                    else:
                        if self.opts.empty == 'skip':
                            # empty tile, skip
                            debug("%r: empty" % tile)
                            continue
                        # TODO: else?

                    self.backend.commit()

                end = time.perf_counter()
                # info("%r: %f, %f" % (metatile, mid-start, end-mid))

                debug("<== [%s] %r: %s", getpid(), metatile, ('old', mid-start, end-mid))
                self.queues[1].put(('old', metatile, mid-start, end-mid))
                debug("<<< [%s]", getpid())

        else:
            # simulate some work
            start = time.perf_counter()
            time.sleep(randint(0, 30) / 10)
            mid = time.perf_counter()
            if self.opts.tiles is None or tile.z < self.opts.max_zoom:
                for child in metatile.children():
                    if random() <= 0.75 or 2**metatile.z < self.opts.metatile_size:
                        render_children[child] = True
            end = time.perf_counter()

            debug("<== [%s] %r: %s", getpid(), metatile, ('old', mid-start, end-mid))
            self.queues[1].put(('old', metatile, mid-start, end-mid))
            debug("<<< [%s]", getpid())

        return render_children


    def notify_children(self, render_children:Dict[map_utils.Tile, bool]) -> None:
        # debug(render_children)
        for tile, render in render_children.items():
            debug("<== [%s] %r: %s", getpid(), tile, render)
            self.queues[1].put(('new', tile, render))
            debug("<<< [%s]", getpid())


    def loop(self):
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

        debug('%s looping the loop', self)
        while True:
            # Fetch a tile from the queue and render it
            t:Optional[map_utils.MetaTile] = self.queues[0].get()
            debug("[%s] ==> %r" % (getpid(), t, ))
            if t is None:
                # self.q.task_done()
                debug('[%s] ending loop' % getpid())
                break

            skip:bool
            if self.opts.skip_existing or self.opts.skip_newer is not None:
                debug('[%s] skip test existing:%s, newer:%s',
                       getpid(), self.opts.skip_existing, self.opts.skip_newer)
                skip = True

                for tile in t.tiles: # type: map_utils.Tile
                    if self.opts.skip_existing:
                        skip = skip and self.backend.exists(tile.z, tile.x, tile.y)
                    else:
                        skip= ( skip and
                                self.backend.newer_than(tile.z, tile.x, tile.y,
                                                        self.opts.skip_newer))
            else:
                skip = False

            render_children:Dict[map_utils.Tile, bool] = {}
            if not skip:
                render_children = self.render_metatile(t)
            else:
                self.queues[1].put(('skept', t))

                # but notify the children, so they get a chance to be rendered
                for child in t.children():
                    # we have no other info about whether they should be
                    # rendered or not, so render them just in case. at worst,
                    # they could either be empty tiles or too new too
                    render_children[child] = True

            self.notify_children(render_children)

            # self.q.task_done()


class Master:
    def __init__(self, opts) -> None:
        self.opts = opts
        self.renderers = {}
        # we need at least space for the initial batch
        self.work_stack = RenderStack(opts.max_zoom)

        if self.opts.parallel == 'fork':
            debug('forks, using mp.Queue()')

            # work_out queue is size 1, so higher zoom level tiles don't pile up
            # there if there are lower ZL tiles ready in the work_stack.
            self.queues = (multiprocessing.Queue(1),
                           multiprocessing.Queue(4*self.opts.threads))
        else:
            debug('threads or single, using queue.Queue()')
            # TODO: this and the warning about mapnik and multithreads
            self.queues = (Queue(32), None)


    def tiles_per_metatile(self, zoom):
        return min(self.opts.metatile_size, 2**zoom) ** 2


    def render_tiles(self) -> None:
        debug("render_tiles(%s)", self.opts)

        backends:Dict[str,Any] = dict(
            tiles=  map_utils.DiskBackend,
            mbtiles=map_utils.MBTilesBackend,
            )

        backend = backends[self.opts.format](self.opts.tile_dir, self.opts.bbox)

        # Launch rendering threads
        for i in range(self.opts.threads):
            renderer = RenderThread(self.opts, backend, self.queues)

            if self.opts.parallel != 'single':
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

        if not os.path.isdir(self.opts.tile_dir):
            debug("creating dir %s", self.opts.tile_dir)
            os.makedirs(self.opts.tile_dir, exist_ok=True)

        initial_metatiles = []
        if self.opts.tiles is None:
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

        if self.opts.parallel == 'single':
            self.queues[0].put(None)
            renderer.loop()

        self.loop(initial_metatiles)
        self.finish()


    def loop(self, initial_metatiles) -> None:
        work_out, work_in = self.queues
        # for each tile that was sent to be worked on, 4 should return
        went_out, came_back, tiles_to_render = 0, 0, 0

        for t in initial_metatiles:
            debug("... %r" % (t, ))
            self.work_stack.push(t)
            # make sure they're rendered!
            self.work_stack.notify(t, True)

            if self.opts.tiles is not None:
                tiles_to_render += self.tiles_per_metatile(t.z)
                # debug("%r: %d", t, tiles_to_render)

        if self.opts.tiles is None:
            first_tiles = len(initial_metatiles)
            tiles_to_render = first_tiles * pyramid_tile_count(opts.min_zoom, opts.max_zoom)

        tiles_rendered = tiles_skept = 0

        # I could get to the pipes used for the Queues, but it's useless, as
        # they're constantly ready. keep the probing version, so select()ing on
        # them leads to a tight loop
        while self.work_stack.size() > 0 or went_out > came_back:
            debug("ws.size(): %s; wo > cb: %d > %d", self.work_stack.size(),
                  went_out, came_back)
            # TODO: move this try outer
            try:
                while True:
                    try:
                        # pop from there,
                        new_work = self.work_stack.pop()  # map_utils.MetaTile
                    except IndexError:
                        debug('out: timeout!')
                        break
                    else:
                        if new_work is not None:
                            try:
                                # push in the writer
                                work_out.put(new_work, True, .1)  # 1/10s timeout
                            except queue.Full:
                                # debug('work_out full, not confirm()ing.')
                                break
                            else:
                                self.work_stack.confirm()
                                went_out += 1
                                debug("--> %r" % (new_work, ))
                        else:
                            break

                # pop from the reader,
                while True:
                    try:
                        # 1/10s timeout
                        type, *data = work_in.get(True, .1)  # type: str, Any
                        debug("<-- %s: %r" % (type, data))
                    except queue.Empty:
                        # debug('in: timeout!')
                        break
                    else:
                        if type == 'new':
                            tile, render = data
                            if tile in self.opts.bbox:
                                self.work_stack.notify(tile, render)
                                if not render:
                                    tiles_skept += 1
                            else:
                                # do not render tiles out of the bbox
                                debug("out of bbox, out of mind")
                                self.work_stack.notify(tile, False)
                                # we count this one and all it descendents as rendered
                                tiles_skept += ( pyramid_tile_count(tile.z, opts.max_zoom) *
                                                 self.tiles_per_metatile(tile.z) )
                                info("[%d+%d/%d: %7.3f%%]", tiles_rendered,
                                    tiles_skept, tiles_to_render,
                                    (tiles_rendered + tiles_skept) / tiles_to_render * 100)


                        elif type == 'old':
                            tile, render_time, saving_time = data
                            tiles_rendered += self.tiles_per_metatile(tile.z)
                            came_back += 1

                            info("[%d+%d/%d: %7.3f%%] %r: %8.3f,  %8.3f",
                                 tiles_rendered, tiles_skept, tiles_to_render,
                                 (tiles_rendered + tiles_skept) / tiles_to_render * 100,
                                 tile, render_time, saving_time)

                        elif type == 'skept':
                            tile, = data
                            tiles_skept += self.tiles_per_metatile(tile.z)
                            came_back += 1

                            if self.opts.skip_existing:
                                message = "present, skipping"
                            else:
                                message = "too new, skipping"

                            info("[%d+%d/%d: %7.3f%%] %r: %s",
                                 tiles_rendered, tiles_skept, tiles_to_render,
                                 (tiles_rendered + tiles_skept) / tiles_to_render * 100,
                                 tile, message)
            except KeyboardInterrupt as e:
                debug(e)
                self.finish()
                raise SystemExit("Ctrl-c detected, exiting...")

        # the weird - 3* thing is because low ZLs don't have 4 children
        # for metatile sizes > 1
        # for instance, metatile_size==8 -> Zls 1, 2, 3 have only one metatile
        while went_out*4 - 3*math.log2(self.opts.metatile_size) > came_back:
            debug("%d <-> %d", went_out*4, came_back)
            type, *data = work_in.get(True)
            debug("<-- %r", data)

            if type == 'old':
                tile, render_time, saving_time = data
                tiles_rendered += self.tiles_per_metatile(tile.z)

                info("[%d+%d/%d: %7.3f%%] %r: %8.3f,  %8.3f",
                        tiles_rendered, tiles_skept, tiles_to_render,
                        (tiles_rendered + tiles_skept) / tiles_to_render * 100,
                        tile, render_time, saving_time)

            came_back += 1

        info("[%d+%d/%d: %7.3f%%]", tiles_rendered,
             tiles_skept, tiles_to_render,
             (tiles_rendered + tiles_skept) / tiles_to_render * 100)
        debug('out!')


    def finish(self):
        if self.opts.parallel!='single':
            debug('finishing threads/procs')
            # Signal render threads to exit by sending empty request to queue
            for i in range(self.opts.threads):
                debug("--> None")
                self.queues[0].put(None)

            # wait for pending rendering jobs to complete
            if not self.opts.parallel == 'fork':
                self.queues[0].join()
            else:
                self.queues[0].close()
                self.queues[0].join_thread()

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
    parser.add_argument('-E', '--empty',         dest='empty',     default='skip', choices=('skip', 'link', 'write'))

    parser.add_argument('-d', '--debug',         dest='debug',     default=False, action='store_true')
    parser.add_argument(      '--dry-run',       dest='dry_run',   default=False, action='store_true')
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
    # os.chdir(os.path.dirname(opts.mapfile))
    opts.mapfile = os.path.basename(opts.mapfile)

    # pick bbox from bboxes.ini
    if opts.bbox_name is not None:
        a = map_utils.Atlas([ opts.bbox_name ])
        opts.bbox = map_utils.BBox(a.maps[opts.bbox_name].bbox, opts.max_zoom)
    else:
        opts.bbox = map_utils.BBox(opts.bbox, opts.max_zoom)

    if opts.parallel == 'single':
        opts.threads = 1

    return opts


if __name__  ==  "__main__":
    opts = parse_args()

    master = Master(opts)
    master.render_tiles()
