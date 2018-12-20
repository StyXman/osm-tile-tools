#!/usr/bin/env python3

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

try:
    import mapnik2 as mapnik
except:
    import mapnik

import map_utils


import logging
from logging import debug, info, exception
long_format = "%(asctime)s %(name)16s:%(lineno)-4d (%(funcName)-21s) %(levelname)-8s %(message)s"
short_format = "%(asctime)s %(message)s"

from typing import Optional, List, Set, Dict, Any

try:
    NUM_CPUS = multiprocessing.cpu_count()
except NotImplementedError:
    NUM_CPUS = 1


def floor(i: int, base: int=1) -> int:
    """Round down i to the closest multiple of base."""
    return base * (i // base)


def pyramid_count(min_zoom, max_zoom):
    return sum([ 4**i for i in range(max_zoom - min_zoom + 1) ])


def time2hms(t):
    h = int(t / 3600.0)
    m = int((t - h * 3600) / 60)
    s = int(t) % 60

    return (h, m, s)


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
    def __init__(self, max_zoom:int) -> None:
        # I don't need order here, it's (probably) better if I validate tiles
        # as soon as possible
        # self.first:Optional[map_utils.MetaTile] = None
        # self.ready:List[map_utils.Tile] = []
        self.first = None
        self.ready = []
        self.max_zoom = max_zoom


    def push(self, metatile:map_utils.MetaTile) -> None:
        # debug("%s, %s, %s", self.first, self.ready, self.to_validate)
        if self.first is not None:
            self.ready.insert(0, self.first)

        self.first = metatile


    def pop(self) -> map_utils.MetaTile:
        return self.first


    def confirm(self) -> None:
        """Mark the top of the stack as sent to render, factually pop()'ing it."""
        if self.first is not None:
            # metatile:map_utils.MetaTile = self.first
            metatile = self.first

        # t:Optional[map_utils.Tile] = None
        t = None
        if len(self.ready) > 0:
            t = self.ready.pop(0)

        self.first = t
        # debug("%s, %s, %s", self.first, self.ready, self.to_validate)


    def size(self) -> int:
        # debug("%s, %s, %s", self.first, self.ready, self.to_validate)
        # HACK: int(bool) ∈ (0, 1)
        # ans:int = int(self.first is not None) + len(self.ready)
        ans = int(self.first is not None) + len(self.ready)
        # debug(ans)
        return ans


RenderChildren = Dict[map_utils.Tile, bool]
class RenderThread:
    def __init__(self, opts, input, output) -> None:
        self.opts = opts
        self.input = input
        self.output = output

        # self.metatile_size:int = opts.metatile_size
        # self.image_size:int = self.opts.tile_size * self.metatile_size
        self.metatile_size = opts.metatile_size
        self.image_size = self.opts.tile_size * self.metatile_size

        if self.opts.parallel == 'single':
            # RenderThread.loop() is not called in single mode
            # so do this here
            self.pid = getpid()
            self.load_map()


    def render_metatile(self, metatile:map_utils.MetaTile) -> Dict[map_utils.Tile, bool]:
        # get LatLong (EPSG:4326)
        l0 = metatile.coords[0]
        l1 = metatile.coords[1]

        # this is the only time where we convert manually into WebMerc
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

        bail_out = True

        # handling C-c: if we're rendering, the exception won't be raised until
        # mapnik has finished, and throwing away that work would be a shame
        # critical section, disable signals
        if self.opts.parallel != 'single':
            sig = signal(SIGINT, SIG_IGN)

        start = time.perf_counter()
        if not self.opts.dry_run:
            im = mapnik.Image(self.image_size, self.image_size)
            # Render image with default Agg renderer
            debug('[%s] rende...', self.pid)
            # TODO: handle exception, send back into queue
            mapnik.render(self.m, im)
            debug('[%s] ...ring!', self.pid)
            mid = time.perf_counter()

            # TODO: all this is on a single tile, no a metatile

            # converting to png256 is the fastest I have found so far:
            # python3.6 -m timeit -s 'import mapnik; im = mapnik.Image.fromstring(open("Attic/tmp/369.png", "br").read())' 'data = im.tostring("png256")'
            # 100 loops, best of 3: 7.72 msec per loop
            # python3.6 -m timeit -s 'import mapnik; im = mapnik.Image.fromstring(open("Attic/tmp/369.png", "br").read())' 'data = im.tostring()'
            # 100000 loops, best of 3: 13.8 usec per loop
            # python3.6 -m timeit -s 'import mapnik, bz2; im = mapnik.Image.fromstring(open("Attic/tmp/369.png", "br").read())' 'c = bz2.BZ2Compressor(); c.compress(im.tostring()); data = c.flush()'
            # 10 loops, best of 3: 20.3 msec per loop
            # python3.6 -m timeit -s 'import mapnik, gzip; im = mapnik.Image.fromstring(open("Attic/tmp/369.png", "br").read())' 'data = gzip.compress(im.tostring())'
            # 10 loops, best of 3: 27.7 msec per loop
            # python3.6 -s -m timeit -s 'import mapnik, lzma; im = mapnik.Image.fromstring(open("Attic/tmp/369.png", "br").read())' "c = lzma.LZMACompressor(); c.compress(im.tostring()); data = c.flush()"
            # 10 loops, best of 3: 92 msec per loop

            # TODO:
            # but bz2 compresses the best, 52714 png vs 49876 bzip vs 70828 gzip vs 53032 lzma

            metatile.im = im.tostring('png256')
            end = time.perf_counter()
        else:
            debug('[%s] thumbtumbling', self.pid)
            time.sleep(randint(0, 30) / 10)
            mid = time.perf_counter()
            end = time.perf_counter()

        metatile.render_time = mid - start
        metatile.serializing_time = end - mid
        bail_out = False

        debug("[%s] putting %r", self.pid, metatile)
        self.output.put(metatile)
        debug("[%s] put! (%d)", self.pid, self.output.qsize())

        # end critical section, restore signal
        if self.opts.parallel != 'single':
            signal(SIGINT, sig)

        return bail_out


    def load_map(self):
        start = time.perf_counter()

        self.m  = mapnik.Map(self.image_size, self.image_size)
        # Load style XML
        if not self.opts.dry_run:
            mapnik.load_map(self.m, self.opts.mapfile, self.opts.strict)

        end = time.perf_counter()
        info('[%s] Map loading took %.6fs', self.pid, end - start)

        # Obtain <Map> projection
        self.prj = mapnik.Projection(self.m.srs)
        # Projects between tile pixel co-ordinates and LatLong (EPSG:4326)
        self.tileproj = map_utils.GoogleProjection(opts.max_zoom + 1)


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

        info("[%s] finished", self.pid)


    def single_step(self):
        # Fetch a tile from the queue and render it
        debug("[%s] get..", self.pid)
        # metatile:Optional[map_utils.MetaTile] = self.input.get()
        metatile = self.input.get()
        debug("[%s] got! %r", self.pid, metatile)
        if metatile is None:
            # self.q.task_done()
            return True

        bail_out = self.render_metatile(metatile)

        # self.q.task_done()
        return bail_out


# backends:Dict[str,Any] = dict(
backends = dict(
    tiles=   map_utils.DiskBackend,
    mbtiles= map_utils.MBTilesBackend,
    mod_tile=map_utils.ModTileBackend,
    test=    map_utils.TestBackend,
    )


class StormBringer:
    def __init__(self, opts, backend, input, output):
        self.opts = opts
        self.backend = backend
        self.input = input
        self.output = output

        if self.opts.parallel == 'single':
            # StormBringer.loop() is not called in single mode
            # so do this here
            self.pid = getpid()


    def loop(self):
        self.pid = getpid()

        debug('[%s] curling the curl', self.pid)

        while self.single_step():
            pass

        debug('done')


    def single_step(self):
        debug('[%s] >... (%d)', self.pid, self.input.qsize())
        metatile = self.input.get(True)
        debug('[%s] ...>', self.pid)

        if metatile is not None:
            debug('[%s] sto...', self.pid)
            self.store_metatile(metatile)
            debug('[%s] ...re!', self.pid)
            self.output.put(metatile)

        return metatile is not None


    def store_metatile(self, metatile):
        # save the image, splitting it in the right amount of tiles
        if not self.opts.dry_run:
            start = time.perf_counter()
            image = mapnik.Image.fromstring(metatile.im)
            mid = time.perf_counter()

            for tile in metatile.tiles:
                self.store_tile(tile, image)

                child = metatile.child(tile)
                # PixelTile does not have
                if child is not None:
                    child.is_empty = child.is_empty and tile.is_empty

            end = time.perf_counter()

            for child in metatile.children():
                # don't render child if: empty; or single tile mode; or too deep
                debug((child.is_empty, self.opts.single_tiles, tile.z, self.opts.max_zoom))
                if ( child.is_empty or self.opts.single_tiles or
                     metatile.z == self.opts.max_zoom ):

                    child.render = False

            # TODO: handle empty and link or write; pyramid stuff
            metatile.deserializing_time = mid - start
            metatile.saving_time = end - mid
        else:
            for child in metatile.children():
                rand = random()
                child.is_empty = (rand >= 0.95 and
                                  2**metatile.z >= self.opts.metatile_size)
                child.render = not (child.is_empty or self.opts.single_tiles or
                                    metatile.z == self.opts.max_zoom)


    def store_tile(self, tile, image):
        i, j = tile.meta_index

        # TODO: Tile.meta_pixel_coords
        # TODO: pass tile_size to MetaTile and Tile
        img = image.view(i*self.opts.tile_size, j*self.opts.tile_size,
                           self.opts.tile_size,   self.opts.tile_size)
        tile.data = img.tostring('png256')

        if not tile.is_empty or self.opts.empty == 'write':
            self.backend.store(tile)
        elif tile.is_empty and self.opts.empty == 'link':
            # TODO
            pass

        self.backend.commit()


class Master:
    def __init__(self, opts) -> None:
        self.opts = opts
        self.renderers = {}
        # we need at least space for the initial batch
        # but do not auto push children in tiles mode
        self.work_stack = RenderStack(opts.max_zoom)

        # counters
        self.went_out = self.came_back = 0
        self.tiles_to_render = self.tiles_rendered = self.tiles_skept = 0

        if self.opts.parallel == 'fork':
            debug('forks, using mp.Queue()')
            # work_out queue is size 1, so higher zoom level tiles don't pile up
            # there if there are lower ZL tiles ready in the work_stack.
            self.new_work = multiprocessing.Queue(1)
            self.store_queue = multiprocessing.Queue(5*self.opts.threads)
            self.info = multiprocessing.Queue(5*self.opts.threads)
        elif self.opts.parallel == 'threads':
            debug('threads, using queue.Queue()')
            # TODO: warning about mapnik and multithreads
            self.new_work = queue.Queue(32)
            self.store_queue = queue.Queue(32)
            self.info = queue.Queue(32)
        else:
            debug('single mode, using queue.Queue()')
            self.new_work = queue.Queue(1)
            self.store_queue = queue.Queue(1)
            self.info = queue.Queue(1)


    def progress(self, metatile, *args, format='%s'):
        percentage = ( (self.tiles_rendered + self.tiles_skept) /
                       self.tiles_to_render * 100 )

        if self.tiles_rendered > 0:
            time_elapsed = time.perf_counter() - self.start
            # calculated only based on what was actually rendered
            # it's broken for the most part of the time (!)
            # but it's better than getting a constant 0:00:00
            # time_per_tile = time_elapsed / ( self.tiles_rendered + self.tiles_skept )
            time_per_tile = time_elapsed / self.tiles_rendered
            debug((time_elapsed, time_per_tile))
            eta = ( (self.tiles_to_render - self.tiles_rendered - self.tiles_skept) *
                    time_per_tile )

            eta_h, eta_m, eta_s = time2hms(eta)

            format = "[%d+%d/%d: %7.4f%%] %r: " + format + " [ETA: %d:%02d:%02d]"
            info(format, self.tiles_rendered, self.tiles_skept, self.tiles_to_render,
                 percentage, metatile, *args, eta_h, eta_m, eta_s)
        else:
            format = "[%d+%d/%d: %7.4f%%] %r: " + format + " [ETA: ∞]"
            info(format, self.tiles_rendered, self.tiles_skept, self.tiles_to_render,
                 percentage, metatile, *args)


    def render_tiles(self) -> None:
        debug("render_tiles(%s)", self.opts)

        self.backend = backends[self.opts.format](self.opts.tile_dir, self.opts.bbox)

        # Launch rendering threads
        if self.opts.parallel != 'single':
            for i in range(self.opts.threads):
                renderer = RenderThread(self.opts, self.new_work, self.store_queue)

                if self.opts.parallel == 'fork':
                    debug('mp.Process()')
                    render_thread = multiprocessing.Process(target=renderer.loop)
                elif self.opts.parallel == 'threads':
                    debug('th.Thread()')
                    render_thread = threading.Thread(target=renderer.loop)

                render_thread.start()

                if self.opts.parallel:
                    debug("Started render thread %s", render_thread.name)
                else:
                    debug("Started render thread %s", render_thread.getName())

                self.renderers[i] = render_thread

            if self.opts.parallel == 'fork':
                sb = StormBringer(self.opts, self.backend, self.store_queue, self.info)
                self.store_thread = multiprocessing.Process(target=sb.loop)
                self.store_thread.start()
        else:
            self.renderer = RenderThread(self.opts, self.new_work, self.store_queue)
            self.store_thread = StormBringer(self.opts, self.backend, self.store_queue,
                                             self.info)


        if not os.path.isdir(self.opts.tile_dir):
            debug("creating dir %s", self.opts.tile_dir)
            os.makedirs(self.opts.tile_dir, exist_ok=True)

        initial_metatiles = []
        if not self.opts.single_tiles:
            # attributes used a lot, so hold them in local vars
            bbox = self.opts.bbox
            tile_size = self.opts.tile_size
            metatile_size = self.opts.metatile_size
            metatile_pixel_size = metatile_size * tile_size
            min_zoom = self.opts.min_zoom

            debug('rendering bbox %s: %s', self.opts.bbox_name, bbox)
            # debug(bbox.lower_left)
            # debug(bbox.upper_right)
            w, s = map_utils.tileproj.lon_lat2pixel(bbox.lower_left, min_zoom)
            e, n = map_utils.tileproj.lon_lat2pixel(bbox.upper_right, min_zoom)
            # debug("%r, %r, %r, %r", w, s, e, n)
            # debug("%d", 2**min_zoom)

            w =  w // metatile_pixel_size      * metatile_size
            s = (s // metatile_pixel_size + 1) * metatile_size
            e = (e // metatile_pixel_size + 1) * metatile_size
            n =  n // metatile_pixel_size      * metatile_size
            # debug("%r, %r, %r, %r", w, s, e, n)
            # debug("%sx%s", list(range(w, e, metatile_size)), list(range(n, s, metatile_size)))

            count = 0
            info('Creating initial metatiles...')
            for x in range(w, e, metatile_size):
                for y in range(n, s, metatile_size):
                    metatile = map_utils.MetaTile(min_zoom, x, y, metatile_size,
                                                  tile_size)
                    initial_metatiles.append(metatile)
                    count += 1
                    if count % 1000 == 0:
                        info('%d...' % count)
            info("%d initial metatiles created." % count)
        else:
            # TODO: if possible, order them in depth first/proximity? fashion.
            debug('rendering individual tiles')
            initial_metatiles = self.opts.tiles

        try:
            self.loop(initial_metatiles)
        except KeyboardInterrupt as e:
            raise SystemExit("Ctrl-c detected, exiting...")
        except Exception as e:
            exception(e)
        finally:
            debug('out!')
            self.finish()


    def push_all_children(self, metatile):
        if metatile.z < self.opts.max_zoom and self.opts.push_children:
            for child in metatile.children():
                # we have no other info about whether they should be
                # rendered or not, so render them just in case. at worst,
                # they could either be empty tiles or too new too
                self.work_stack.push(child)


    def should_render(self, metatile):
        # TODO: move all these checks to another thread/process.
        # skip:bool
        if metatile in self.opts.bbox:
            if self.opts.skip_existing or self.opts.skip_newer is not None:
                debug('skip test existing:%s, newer:%s', self.opts.skip_existing,
                    self.opts.skip_newer)
                skip = True

                for tile in metatile.tiles: # type: map_utils.Tile
                    if self.opts.skip_existing:
                        # TODO: missing as present?
                        skip = skip and self.backend.exists(tile)
                        # debug('skip: %s', skip)
                        message = "present, skipping"
                    else:
                        skip= ( skip and
                                self.backend.newer_than(tile, self.opts.skip_newer,
                                                        self.opts.missing_as_new) )
                        # debug('skip: %s', skip)
                        message = "too new, skipping"

                if skip:
                    self.work_stack.confirm()
                    self.tiles_skept += len(metatile.tiles)
                    self.progress(metatile, message)

                    # notify the children, so they get a chance to be rendered
                    self.push_all_children(metatile)
            else:
                skip = False
                # debug('skip: %s', skip)
        else:
            # do not render tiles out of the bbox
            skip = True
            self.work_stack.confirm()

            # we count this one and all it descendents as skept
            self.tiles_skept += ( len(metatile.tiles) *
                                  pyramid_count(metatile.z, opts.max_zoom) )
            self.progress(metatile, "out of bbox")

        return not skip


    def loop(self, initial_metatiles) -> None:
        self.start = time.perf_counter()

        for metatile in initial_metatiles:
            debug("... %r", (metatile, ))
            self.work_stack.push(metatile)

        first_tiles = len(initial_metatiles)
        if self.opts.single_tiles:
            self.tiles_to_render = first_tiles * len(metatile.tiles)
        else:
            # all initial_metatiles are from the same zoom level
            self.tiles_to_render = ( first_tiles * len(metatile.tiles) *
                                     pyramid_count(opts.min_zoom, opts.max_zoom) )

        # I could get to the pipes used for the Queues, but it's useless, as
        # they're constantly ready, so select()ing on them leads to a tight loop
        # keep the probing version
        while ( self.work_stack.size() > 0 or
                self.went_out > self.came_back or
                self.tiles_to_render > self.tiles_rendered + self.tiles_skept ):

            tight_loop = True

            # the doc says this is unrealiable, but we don't care
            # full() can be inconsistent only if when we test is false
            # and when we put() is true, but only the master is writing
            # so this cannot happen
            while not self.new_work.full():
                tight_loop = False

                # pop from there,
                metatile = self.work_stack.pop()  # map_utils.MetaTile
                if metatile is not None:
                    # TODO: move to another thread
                    if not self.should_render(metatile):
                        continue

                    # push in the writer
                    self.new_work.put(metatile, True, .1)  # 1/10s timeout
                    self.work_stack.confirm()
                    self.went_out += 1
                    debug("--> %r", (metatile, ))

                    if self.opts.parallel == 'single':
                        self.renderer.single_step()
                        # also, get out of this place, so we can clean up
                        # in the next loop
                        break
                else:
                    # no more work to do
                    tight_loop = True
                    break

            if self.opts.parallel == 'single' and self.store_queue.qsize() > 0:
                self.store_thread.single_step()

            # pop from the reader,
            while not self.info.empty():
                tight_loop = False

                # 1/10s timeout
                data = self.info.get(True, .1)  # type: str, Any
                debug("<-- %s", data)

                self.handle_new_work(data)

            if tight_loop:
                # we didn't do anything, so sleep for a while
                # otherwise, this becomes a thigh loop
                time.sleep(0.1)

        total_time = time.perf_counter() - self.start
        h, m, s = time2hms(total_time)

        info("total time: %3d:%02d:%02d", h, m, s)
        metatiles_rendered = self.tiles_rendered / self.opts.metatile_size**2

        if metatiles_rendered != 0:
            info("%8.3f s/metatile", total_time / metatiles_rendered)
        info("%8.3f metatile/s", metatiles_rendered / total_time)

        debug('out!')


    def handle_new_work(self, metatile):
        # an empty metatile will be accounted as rendered,
        # but the children can be pruned
        if self.opts.push_children:
            for child in reversed(metatile.children()):
                debug("%r: %s, %s", child, child.render, child.is_empty)
                if child.render:
                    self.work_stack.push(child)
                elif child.is_empty:
                    self.tiles_skept += ( len(child.tiles) *
                                          pyramid_count(child.z, opts.max_zoom) )
                    self.progress(child, format="empty")

        self.tiles_rendered += len(metatile.tiles)
        self.came_back += 1

        self.progress(metatile, metatile.render_time, metatile.serializing_time,
                      metatile.deserializing_time, metatile.saving_time,
                      format="%8.3f, %8.3f, %8.3f, %8.3f")


    def finish(self):
        if self.opts.parallel != 'single':
            info('stopping threads/procs')
            # Signal render threads to exit by sending empty request to queue
            for i in range(self.opts.threads):
                info("%d...", (i + 1))
                self.new_work.put(None)

            self.store_queue.put(None)

            while self.went_out > self.came_back:
                debug("%d <-> %d", self.went_out, self.came_back)
                data = self.info.get(True)  # type: str, Any
                debug("<-- %s", data)

                self.handle_new_work(data)

            # wait for pending rendering jobs to complete
            if not self.opts.parallel == 'fork':
                self.new_work.join()
                self.store_thread.join()
            else:
                self.new_work.close()
                self.new_work.join_thread()

            for i in range(self.opts.threads):
                self.renderers[i].join()


def parse_args():
    parser = ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-b', '--bbox',          dest='bbox',      default='-180,-85,180,85', metavar='W,S,E,N')
    group.add_argument('-B', '--bbox-name',     dest='bbox_name', default=None)
    group.add_argument('-T', '--tiles',         dest='tiles',     default= None, nargs='+', metavar='METATILE',
                       help="METATILE can be in the form Z,X,Y or Z/X/Y.")
    group.add_argument('-c', '--coords',        dest='coords',    default=None,
                       help="COORDS can be in form 'Lat,Lon', ´Lat/Lon'.")
    group.add_argument('-L', '--longlat',        dest='longlat',    default=None, nargs=2, metavar=('LONG', 'LAT'))

    parser.add_argument('-n', '--min-zoom',      dest='min_zoom',  default=0, type=int)
    parser.add_argument('-x', '--max-zoom',      dest='max_zoom',  default=18, type=int)

    parser.add_argument('-i', '--input-file',    dest='mapfile',   default='osm.xml',
                        help="MapnikXML format.")
    parser.add_argument('-f', '--format',        dest='format',    default='tiles',
                        choices=('tiles', 'mbtiles', 'mod_tile', 'test'))
    parser.add_argument('-o', '--output-dir',    dest='tile_dir',  default='tiles/')

    # TODO: check it's a power of 2
    parser.add_argument('-m', '--metatile-size', dest='metatile_size', default=1, type=int,
                        help='Must be a power of two.')

    parser.add_argument('-t', '--threads',       dest='threads',   default=NUM_CPUS,
                        type=int)
    parser.add_argument('-p', '--parallel-method', dest='parallel', default='fork',
                        choices=('threads', 'fork', 'single'))

    parser.add_argument('-X', '--skip-existing', dest='skip_existing', default=False,
                        action='store_true')
    # TODO: newer than input_file
    parser.add_argument('-N', '--skip-newer',    dest='skip_newer', default=None,
                        type=int, metavar='DAYS')
    parser.add_argument(      '--missing-as-new',  dest='missing_as_new', default=False, action='store_true',
                        help="missing tiles in a meta tile count as newer, so we don't re-render metatiles with empty tiles.")
    parser.add_argument('-E', '--empty',         dest='empty',     default='skip',
                        choices=('skip', 'link', 'write'))

    parser.add_argument(      '--debug',         dest='debug',     default=False, action='store_true')
    parser.add_argument('-l', '--log-file',      dest='log_file',  default=None)
    parser.add_argument(      '--dry-run',       dest='dry_run',   default=False, action='store_true')

    parser.add_argument(      '--strict',        dest='strict',    default=False, action='store_true',
                        help='''Use Mapnik's strict mode.''')

    # TODO: buffer size (256?)
    opts = parser.parse_args()

    if opts.log_file is not None:
        root = logging.getLogger()

        # this is more or less the same thing we get with basicConfig()
        stderr_handler = logging.StreamHandler()
        stderr_handler.setFormatter(logging.Formatter(short_format))
        stderr_handler.setLevel(logging.INFO)
        root.addHandler(stderr_handler)

        file_handler = logging.FileHandler(opts.log_file)
        if opts.debug:
            file_handler.setFormatter(logging.Formatter(long_format))
            file_handler.setLevel(logging.DEBUG)
            # the root logger will be pre-filtering by level
            # so we need to set its level to the lowest possible
            root.setLevel(logging.DEBUG)
            root.addHandler(file_handler)
        else:
            file_handler.setFormatter(logging.Formatter(short_format))
            file_handler.setLevel(logging.INFO)
            root.setLevel(logging.INFO)

    else:
        if opts.debug:
            logging.basicConfig(level=logging.DEBUG, format=long_format)
        else:
            logging.basicConfig(level=logging.INFO, format=short_format)

    if opts.format == 'tiles' and opts.tile_dir[-1] != '/':
        # we need the trailing /, it's actually a series of BUG s in render_tiles()
        opts.tile_dir += '/'

    opts.tile_dir = os.path.abspath(opts.tile_dir)
    if opts.skip_newer is not None:
        opts.skip_newer = ( datetime.datetime.now() -
                            datetime.timedelta(days=opts.skip_newer) )

    if opts.bbox_name is not None:
        # pick bbox from bboxes.ini
        atlas = map_utils.Atlas([ opts.bbox_name ])
        opts.bbox = map_utils.BBox(atlas.maps[opts.bbox_name].bbox, opts.max_zoom)
    else:
        opts.bbox = map_utils.BBox([ float(s) for s in opts.bbox.split(',') ], opts.max_zoom)

    if opts.format in ('mod_tile', 'test'):
        opts.tile_size = 8 * 256
        if opts.metatile_size < 8:
            opts.metatile_size = 8

        # normalize values
        opts.metatile_size //= 8
        if opts.tiles is not None:
            metatiles = []

            for tile_spec in opts.tiles:
                z, x, y = map_utils.tile_spec2zxy(tile_spec)

                # normalize
                x //= 8
                y //= 8

                metatile = map_utils.MetaTile(z, x, y, opts.metatile_size,
                                              opts.tile_size)
                metatiles.append(metatile)

            opts.tiles = metatiles
    else:
        opts.tile_size = 256
        if opts.tiles is not None:
            metatiles = []

            for tile_spec in opts.tiles:
                z, x, y = map_utils.tile_spec2zxy(tile_spec)
                metatile = map_utils.MetaTile(z, x, y, opts.metatile_size,
                                              opts.tile_size)
                metatiles.append(metatile)

            opts.tiles = metatiles

    if opts.coords is not None or opts.longlat is not None:
        opts.tile_size = 1024

        if opts.coords is not None:
            # input is Lat,Lon but tileproj works with Lon,Lat
            lat, long = opts.coords.split('/')
            opts.coords = (float(long), float(lat))
        elif opts.longlat is not None:
            # input is Lon,Lat already
            long, lat = opts.longlat
            opts.coords = (float(long), float(lat))

        debug(opts.coords)

        metatiles = []

        for z in range(opts.min_zoom, opts.max_zoom + 1):
            # TODO: maybe move this conversion to PixelTile
            x, y = map_utils.tileproj.lon_lat2pixel(opts.coords, z)
            tile = map_utils.PixelTile(z, x, y, 1024)
            metatiles.append(tile)

        opts.tiles = metatiles

    # semantic opts
    opts.single_tiles = opts.tiles is not None
    opts.push_children = not opts.single_tiles

    return opts


if __name__  ==  "__main__":
    opts = parse_args()

    master = Master(opts)

    # fixes for locally installed mapnik
    mapnik.register_fonts ('/usr/share/fonts/')
    mapnik.register_plugins ('/home/mdione/local/lib/mapnik/input/')

    master.render_tiles()
