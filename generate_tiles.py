#! /usr/bin/env python3

# https://github.com/openstreetmap/mapnik-stylesheets/blob/master/generate_tiles.py with *LOTS* of enhancements

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

import pyproj

import map_utils
import utils
import tiles


import logging
from logging import debug, info, exception, warning
long_format = "%(asctime)s %(name)16s:%(lineno)-4d (%(funcName)-21s) %(levelname)-8s %(message)s"
short_format = "%(asctime)s %(message)s"

# EPSGs
WebMerc = 3857
LonLat = 4326

from typing import Optional, List, Set, Dict, Any


# TODO: this gives very bad numbers because if we start from a low enough ZL many tiles will be discarded
# replace it with an algorithm that precounts all the tiles that are really going to be rendered
# down there there m,ust be a part of the algo that gets all the tiles for ZL x that match the original bbox
# TODO: check whether if it's a generator
# TODO: or replace with something that simultaes going down the pyramid; in fact, it could be a dry run version
# of the actual rendering algo


class RenderStack:
    '''
    A render stack implemented with a list... and more.

    Although this is implemented with a list, I prefer the semantic of these
    methods and the str() representation given by the list being pop from/push
    into the left.

    The stack has a first element, which is the one ready to be pop()'ed.
    Because this element might need to be returned into the stack, there's the confirm()
    method which actually pops it, leaving the next one ready.

    The stack also autofills with children when we pop an element. Because
    these children might not be needed to be rendered, they're stored in
    another list, to_validate.

    stack.push(e)
    e = stack.pop()
    stack.confirm()
    '''
    def __init__(self, max_zoom:int) -> None:
        # I don't need order here, it's (probably) better if I validate tiles
        # as soon as possible
        self.first:Optional[tiles.MetaTile] = None
        self.ready:List[tiles.MetaTile] = []
        self.max_zoom = max_zoom


    def push(self, metatile:tiles.MetaTile) -> None:
        # debug("%s, %s, %s", self.first, self.ready, self.to_validate)
        if self.first is not None:
            self.ready.insert(0, self.first)

        self.first = metatile


    def pop(self) -> Optional[tiles.MetaTile]:
        return self.first


    def confirm(self) -> None:
        '''Mark the top of the stack as sent to render, factually pop()'ing it.'''
        if self.first is not None:
            # metatile:tiles.MetaTile = self.first
            metatile = self.first

        # t:Optional[tiles.Tile] = None
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


RenderChildren = Dict[tiles.Tile, bool]
class RenderThread:
    def __init__(self, opts, input, output) -> None:
        self.opts = opts
        self.input = input
        self.output = output

        # self.metatile_size:int = opts.metatile_size
        # self.image_size:int = self.opts.tile_size * self.metatile_size
        self.metatile_size = opts.metatile_size

        self.store_thread = None


    def render(self, metatile:tiles.MetaTile) -> Dict[tiles.Tile, bool]:
        # get LatLong (EPSG:4326)
        w, n = metatile.coords[0]
        e, s = metatile.coords[1]
        # debug("lonlat: %r %r %r %r", w, s, e, n)

        w, n = ( int(x) for x in self.transformer.transform(n, w) )
        e, s = ( int(x) for x in self.transformer.transform(s, e) )
        # debug("webmerc: %r %r %r %r", w, s, e, n)

        # Bounding box for the tile
        if hasattr(mapnik, 'mapnik_version') and mapnik.mapnik_version() >= 800:
            # lower left and upper right corner points.
            bbox = mapnik.Box2d(w, s, e, n)
        else:
            bbox = mapnik.Envelope(w, s, e, n)

        # debug("bbox: %r", bbox)

        image_size = self.opts.tile_size * min(self.metatile_size, 2**metatile.z)
        self.m.resize(image_size, image_size)
        self.m.zoom_to_box(bbox)
        if self.m.buffer_size < 128:
            self.m.buffer_size = 128

        start = time.perf_counter()
        if not self.opts.dry_run:
            if self.opts.format == 'svg':
                im = cairo.SVGSurface(f"{self.opts.tile_dir}/{self.opts.coords[0][0]}-{self.opts.coords[0][1]}.svg",
                                      self.opts.tile_size, self.opts.tile_size)
            elif self.opts.format == 'pdf':
                im = cairo.PDFSurface(f"{self.opts.tile_dir}/{self.opts.coords[0][0]}-{self.opts.coords[0][1]}.pdf",
                                      self.opts.tile_size, self.opts.tile_size)
            else:
                im = mapnik.Image(image_size, image_size)

            # Render image with default Agg renderer
            debug('[%s] rende...', self.name)
            # TODO: handle exception, send back into queue
            try:
                debug(mapnik.render(self.m, im))
            except Exception as e:
                debug(e)

                mid = time.perf_counter()
                metatile.render_time = mid - start
                metatile.serializing_time = 0

                # render errors are quite bad, bailout
                return False

            debug('[%s] ...ring!', self.name)
            mid = time.perf_counter()

            # TODO: all this is on a single tile, not a metatile

            # converting to png256 is the fastest I have found so far:
            # python3.6 -m timeit -s 'import mapnik; im = mapnik.Image.fromstring(open("Attic/tmp/369.png", "br").read())' 'data = im.tostring("png256")'
            # 100 loops, best of 3: 7.72 msec per loop
            # tostring() looks nice, but I can't rebuild a mapnik.Image from it :(
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

            if not self.opts.store_thread:
                # if there is not a separate store thread, the metatile will go in a non-marshaling queue,
                # so no need tostring() it
                metatile.im = im
            else:
                metatile.im = im.tostring('png256')  # here it's converted only for serialization reasons

            end = time.perf_counter()
        else:
            debug('[%s] thumbtumbling', self.name)
            time.sleep(randint(0, 30) / 10)
            mid = time.perf_counter()
            end = time.perf_counter()

        metatile.render_time = mid - start
        metatile.serializing_time = end - mid

        debug("[%s] putting %r", self.name, metatile)
        self.output.put(metatile)
        debug("[%s] put! (%d)", self.name, self.output.qsize())

        if not self.opts.store_thread and self.output.qsize() > 0:
            # NOTE: mypy complains here that Item "Process" of "Union[Process, StormBringer]" has no attribute "single_step"
            # the solutions are ugly, so I'm leaving it as that
            self.store_thread.single_step()

        return True


    def load_map(self):
        start = time.perf_counter()

        # don't worry about the size, we're going to change it later
        self.m  = mapnik.Map(0, 0)
        # Load style XML
        if not self.opts.dry_run:
            try:
                mapnik.load_map(self.m, self.opts.mapfile, self.opts.mapnik_strict)
            except RuntimeError as e:
                print(f"Error loading map: {e.args[0]}")
                return False

        end = time.perf_counter()
        info('[%s] Map loading took %.6fs', self.name, end - start)

        self.transformer = pyproj.Transformer.from_crs(f'EPSG:{LonLat}', f'EPSG:{WebMerc}')

        # Projects between tile pixel co-ordinates and LatLong (EPSG:4326)
        # this is *not* the same as EPSG:3857 because every zoom level has its own pixel space
        self.tileproj = tiles.GoogleProjection(self.opts.max_zoom + 1)

        return True


    def loop(self):
        # disable SIGINT so C-c/KeyboardInterrupt is handled by Master
        # even in the case of multiprocessing
        sig = signal(SIGINT, SIG_IGN)

        if not self.load_map():
            # TODO: send a ready/failed message to the Master
            return

        info("[%s]: starting...", self.name)
        debug('[%s] looping the loop', self.name)

        while self.single_step():
            pass

        info("[%s] finished", self.name)


    def single_step(self):
        # Fetch a tile from the queue and render it
        debug("[%s] get..", self.name)
        # metatile:Optional[tiles.MetaTile] = self.input.get()
        metatile = self.input.get()
        debug("[%s] got! %r", self.name, metatile)

        if metatile is None:
            # it's the end; send the storage thread a message and finish
            debug("[%s] putting %r", self.name, None)
            self.output.put(None)
            debug("[%s] put! (%d)", self.name, self.output.qsize())

            return False

        return self.render(metatile)


# backends:Dict[str,Any] = dict(
backends = dict(
    tiles=   map_utils.DiskBackend,
    mbtiles= map_utils.MBTilesBackend,
    mod_tile=map_utils.ModTileBackend,
    test=    map_utils.TestBackend,
    # SVGs and PDFs are saved by the renderer itself
    # but we still need to provide a callable
    svg=     lambda *more, **even_more: None,
    pdf=     lambda *more, **even_more: None,
)

default_options = dict(
    png256='t=0',
    jpeg='quality=50',
)


class StormBringer:
    def __init__(self, opts, backend, input, output):
        self.opts = opts
        self.backend = backend
        self.input = input
        self.output = output
        # the amount of threads writing on input
        # this is needed so we can stop only after all the writers sent their last jobs
        self.writers = self.opts.threads
        self.done_writers = 0

        if   self.opts.tile_file_format == 'png':
            self.tile_file_format = 'png256'
        elif self.opts.tile_file_format == 'jpg':
            self.tile_file_format = 'jpeg'

        if self.opts.tile_file_format_options == '':
            self.opts.tile_file_format_options = default_options[self.tile_file_format]

        self.tile_file_format += f":{self.opts.tile_file_format_options}"


    def loop(self):
        # disable SIGINT so C-c/KeyboardInterrupt is handled by Master
        # even in the case of multiprocessing
        sig = signal(SIGINT, SIG_IGN)

        debug('[%s] curling the curl', self.name)

        while self.single_step():
            pass

        debug('[%s] done', self.name)


    def single_step(self):
        debug('[%s] >... (%d)', self.name, self.input.qsize())
        metatile = self.input.get()
        debug('[%s] ...> %s', self.name, metatile)

        if metatile is not None:
            debug('[%s] sto...', self.name)
            self.store_metatile(metatile)
            debug('[%s] ...red!', self.name)
            # we don't need it anymore and *.Queue complains that
            # mapnik._mapnik.Image is not pickle()'able
            metatile.im = None
            self.output.put(metatile)
        else:
            # this writer finished
            self.done_writers += 1
            debug('[%s] %d <-> %d', self.name, self.writers, self.done_writers)

        return self.done_writers != self.writers


    def store_metatile(self, metatile):
        # save the image, splitting it in the right amount of tiles
        if not self.opts.dry_run:
            start = time.perf_counter()
            if not self.opts.store_thread:
                image = metatile.im
            else:
                image = mapnik.Image.frombuffer(metatile.im)
            mid = time.perf_counter()

            for tile in metatile.tiles:
                self.store_tile(tile, image)

                # do not try to compute this for tiles outside the asked range
                if metatile.z < self.opts.max_zoom:
                    child = metatile.child(tile)
                    # PixelTile does not have
                    if child is not None:
                        child.is_empty = child.is_empty and tile.is_empty

            end = time.perf_counter()

            for child in metatile.children():
                # don't render child if: empty; or single tile mode; or too deep
                debug((child.is_empty, self.opts.single_tiles, tile.z, self.opts.max_zoom))
                if child.is_empty or self.opts.single_tiles or metatile.z == self.opts.max_zoom:
                    child.render = False

            metatile.deserializing_time = mid - start
            metatile.saving_time = end - mid
        else:
            # do not try to compute this for tiles outside the asked range
            if metatile.x < self.opts.max_zoom:
                for child in metatile.children():
                    rand = random()
                    # 5% are fake empties
                    child.is_empty = (rand <= 0.05 and 2**metatile.z >= self.opts.metatile_size)
                    child.render = not (child.is_empty or self.opts.single_tiles or metatile.z == self.opts.max_zoom)


    def store_tile(self, tile, image):
        # SVG and PDF are stored by the renderer
        if self.opts.format not in ('svg', 'pdf'):
            i, j = tile.meta_index

            # TODO: Tile.meta_pixel_coords
            # TODO: pass tile_size to MetaTile and Tile
            img = image.view(i*self.opts.tile_size, j*self.opts.tile_size,
                               self.opts.tile_size,   self.opts.tile_size)

            # this seems like duplicated work, but we need one looseless format for serializing
            # and another format for the final tile
            tile.data = img.tostring(self.tile_file_format)

            # debug((len(tile.data), tile.data[41:44]))
            tile.is_empty = len(tile.data) == self.opts.empty_size and tile.data[41:44] == self.opts.empty_color

            if tile.is_empty:
                debug('Skipping empty tile')

            if not tile.is_empty or self.opts.empty == 'write':
                self.backend.store(tile)
            elif tile.is_empty and self.opts.empty == 'link':
                # TODO
                pass

            self.backend.commit()


class Master:
    def __init__(self, opts) -> None:
        self.opts = opts
        self.renderers:Dict[int, Union[multiprocessing.Process, threading.Thread]] = {}
        self.store_thread:Union[multiprocessing.Process, StormBringer]
        # we need at least space for the initial batch
        # but do not auto push children in tiles mode
        self.work_stack = RenderStack(opts.max_zoom)

        # counters
        self.went_out = self.came_back = 0
        self.tiles_to_render = self.tiles_rendered = self.tiles_skipped = 0

        # statistics
        self.median = utils.MedianTracker()

        self.create_infra()


    def create_infra(self):
        # this creates a queue that's not used for on-demand usage, but it's not much, so we don't care
        if self.opts.parallel == 'fork':
            debug('forks, using mp.Queue()')
            # work_out queue is size 1, so initial metatiles don't clog it at the beginning
            # because we need to be able to replace the top with its children to drill down
            # and 'reuse' cache before moving to another area.
            self.new_work = multiprocessing.Queue(1)

            # store_queue and info need enough space to hold the four children of the metatiles
            # returned by all threads and more just in case, otherwise the queue blocks and we get a deadlock
            if not self.opts.store_thread:
                # BUG: why do we still use a queue when we're storing the tiles
                # in the same thread as the one rendering them?
                debug('utils.SimpleQueue')
                self.store_queue = utils.SimpleQueue(5*self.opts.threads)
            else:
                self.store_queue = multiprocessing.Queue(5*self.opts.threads)
            self.info = multiprocessing.Queue(5*self.opts.threads)
        elif self.opts.parallel == 'threads':
            debug('threads, using queue.Queue()')
            # TODO: warning about mapnik and multithreads
            self.new_work = queue.Queue(32)
            if not self.opts.store_thread:
                debug('utils.SimpleQueue')
                self.store_queue = utils.SimpleQueue(32)
            else:
                self.store_queue = queue.Queue(32)
            self.info = queue.Queue(32)
        else:  # 'single'
            debug('single mode, using queue.Queue()')
            self.new_work = queue.Queue(1)
            if not self.opts.store_thread:
                self.store_queue = utils.SimpleQueue(1)
            else:
                self.store_queue = queue.Queue(1)
            self.info = queue.Queue(1)

        self.backend = backends[self.opts.format](self.opts.tile_dir, self.opts.bbox,
                                                  **self.opts.more_opts)

        # Launch rendering threads
        if self.opts.parallel != 'single':
            sb = StormBringer(self.opts, self.backend, self.store_queue, self.info)
            if self.opts.store_thread:
                self.store_thread = self.opts.parallel_factory(target=sb.loop)
                sb.name = self.store_thread.name
                self.store_thread.start()
                debug("Started store thread %s", self.store_thread.name)
            else:
                sb.name = 'store-embedded'
                self.store_thread = sb

            for i in range(self.opts.threads):
                renderer = RenderThread(self.opts, self.new_work, self.store_queue)

                render_thread = self.opts.parallel_factory(target=renderer.loop, name=f"Renderer-{i + 1:03d}")
                renderer.name = render_thread.name

                if not self.opts.store_thread:
                    debug("Store object created, attached to thread")
                    renderer.store_thread = self.store_thread

                render_thread.start()
                debug("Started render thread %s", render_thread.name)

                self.renderers[i] = render_thread
        else:
            # in this case we create the 'thread', but in fact we only use its single_step()
            self.store_thread = StormBringer(self.opts, self.backend, self.store_queue,
                                             self.info)
            self.store_thread.name = 'single-store'
            debug("Store object created, not threaded")
            self.renderer = RenderThread(self.opts, self.new_work, self.store_queue)
            self.renderer.name = 'single-render'
            self.renderer.load_map()
            self.renderer.store_thread = self.store_thread
            debug("Renderer object created, not threaded")

        if not os.path.isdir(self.opts.tile_dir) and not self.opts.format == 'mbtiles':
            debug("creating dir %s", self.opts.tile_dir)
            os.makedirs(self.opts.tile_dir, exist_ok=True)


    def progress(self, metatile, *args, format='%s'):
        percentage = ( (self.tiles_rendered + self.tiles_skipped) /
                       self.tiles_to_render * 100 )

        now = time.perf_counter()
        time_elapsed = now - self.start
        metatile_render_time = sum(metatile.times())

        if metatile_render_time > 0:
            self.median.add(metatile_render_time / len(metatile.tiles))
            debug(self.median.items)

        if self.tiles_rendered > 0:
            time_per_tile_median = self.median.median()
            time_per_tile_all_tiles = time_elapsed / (self.tiles_rendered + self.tiles_skipped)
            time_per_tile_rendered_tiles = time_elapsed / self.tiles_rendered
            time_per_tile = (time_per_tile_all_tiles + time_per_tile_rendered_tiles) / 2
            debug("times: median: %10.6f; all: %10.6f; rendered: %10.6f; calculated: %10.6f",
                  time_per_tile_median, time_per_tile_all_tiles, time_per_tile_rendered_tiles, time_per_tile)

            eta = ( (self.tiles_to_render - self.tiles_rendered - self.tiles_skipped) *
                    time_per_tile ) / self.opts.threads
            debug((self.start, now, time_elapsed, metatile_render_time, time_per_tile, eta))

            format = "[%d+%d/%d: %7.4f%%] %r: " + format + " [Elapsed: %dh%02dm%06.3fs, ETA: %dh%02dm%06.3fs, Total: %dh%02dm%06.3fs]"
            info(format, self.tiles_rendered, self.tiles_skipped, self.tiles_to_render,
                 percentage, metatile, *args, *utils.time2hms(time_elapsed),
                 *utils.time2hms(eta), *utils.time2hms(time_elapsed + eta))
        else:
            format = "[%d+%d/%d: %7.4f%%] %r: " + format + " [Elapsed: %dh%02dm%06.3fs, ETA: ∞, Total: ∞]"
            info(format, self.tiles_rendered, self.tiles_skipped, self.tiles_to_render,
                 percentage, metatile, *args, *utils.time2hms(time_elapsed))


    def metatiles_for_bbox(self):
        result = []

        # attributes used a lot, so hold them in local vars
        bbox = self.opts.bbox
        min_zoom = self.opts.min_zoom
        tile_size = self.opts.tile_size
        # if the ZL is too low, shrink the metatile_size
        metatile_size = min(self.opts.metatile_size, 2**min_zoom)
        metatile_pixel_size = metatile_size * tile_size

        debug('rendering bbox %s: %s', self.opts.bbox_name, bbox)
        # debug(bbox.lower_left)
        # debug(bbox.upper_right)
        w, s = tiles.tileproj.lon_lat2pixel(bbox.lower_left, min_zoom)
        e, n = tiles.tileproj.lon_lat2pixel(bbox.upper_right, min_zoom)
        # debug("pixel ZL%r: %r, %r, %r, %r", min_zoom, w, s, e, n)
        # debug("%d", 2**min_zoom)

        w =  w // metatile_pixel_size      * metatile_size
        s = (s // metatile_pixel_size + 1) * metatile_size
        e = (e // metatile_pixel_size + 1) * metatile_size
        n =  n // metatile_pixel_size      * metatile_size
        # debug("tiles: %r, %r, %r, %r", w, s, e, n)
        # debug("%sx%s", list(range(w, e, metatile_size)), list(range(n, s, metatile_size)))

        count = 0
        info('Creating initial metatiles...')
        for x in range(w, e, metatile_size):
            for y in range(n, s, metatile_size):
                metatile = tiles.MetaTile(min_zoom, x, y, self.opts.metatile_size,
                                          tile_size)
                # TODO: convert this into a generator
                # for that we will need to modify the RenderStack so we have 2 sections, one the generator,
                # another for the chidren stacked on top
                result.append(metatile)
                count += 1
                if count % 1000 == 0:
                    info('%d...' % count)

        info("%d initial metatiles created." % count)

        return result


    def render_tiles(self) -> None:
        debug("render_tiles(%s)", self.opts)

        initial_metatiles = []
        if not self.opts.single_tiles:
            initial_metatiles = self.metatiles_for_bbox()
        else:
            # TODO: if possible, order them in depth first/proximity? fashion.
            debug('rendering individual tiles')
            initial_metatiles = self.opts.tiles

        try:
            self.loop(initial_metatiles)
        except KeyboardInterrupt as e:
            info("Ctrl-c detected, exiting...")
        except Exception as e:
            info('unknown exception caught!')
            exception(str(e))
        finally:
            debug('render_tiles() out!')
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
                debug('skip test existing: %s; newer: %s', self.opts.skip_existing,
                    self.opts.skip_newer)
                skip = True

                for tile in metatile.tiles: # type: tiles.Tile
                    if self.opts.skip_existing:
                        # TODO: missing as present?
                        # NOTE: it's called missing_as_new
                        skip = skip and self.backend.exists(tile)
                        # debug('skip: %s', skip)
                        message = "present, skipping"
                    else:
                        skip = ( skip and
                                 self.backend.newer_than(tile, self.opts.skip_newer,
                                                         self.opts.missing_as_new) )
                        # debug('skip: %s', skip)
                        message = "too new, skipping"

                if skip:
                    self.work_stack.confirm()
                    self.tiles_skipped += len(metatile.tiles)
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

            # we count this one and all it descendents as skipped
            self.tiles_skipped += ( len(metatile.tiles) *
                                    utils.pyramid_count(metatile.z, opts.max_zoom) )
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
                                     utils.pyramid_count(opts.min_zoom, opts.max_zoom) )

        while ( self.work_stack.size() > 0 or
                self.went_out > self.came_back or
                self.tiles_to_render > self.tiles_rendered + self.tiles_skipped ):

            tight_loop = self.single_step()

            if tight_loop:
                # if there's nothing to do, we take a 1/10th second nap
                time.sleep(0.1)

        total_time = time.perf_counter() - self.start
        h, m, s = utils.time2hms(total_time)

        info("total time: %3dh%02dm%02ds", h, m, s)
        metatiles_rendered = self.tiles_rendered / self.opts.metatile_size**2

        if metatiles_rendered != 0:
            info("%8.3f s/metatile", total_time / metatiles_rendered)
            info("%8.3f metatile/s", metatiles_rendered / total_time * opts.threads)
            info("%8.3f s/tile", total_time / self.tiles_rendered)
            info("%8.3f tile/s", self.tiles_rendered / total_time * opts.threads)

        debug('loop() out!')



    def single_step(self):
        # I could get to the pipes used for the Queues, but it's useless, as they're constantly ready
        # they're really controlled by the semaphores guarding those pipes
        # so select()ing on them leads to a tight loop
        # keep the probing version

        tight_loop = True

        # we have two Queues to manage, new_work and info
        # neither new_work.push() nor info.pop() should block, but luckily we're the only thread
        # writing on the former and reading from the latter

        # so we simply test-and-write and test-and-read

        # the doc says this is unreliable, but we don't care
        # full() can be inconsistent only if when we test is false
        # and when we put() is true, but only the master is writing
        # so no other thread can fill the queue
        while not self.new_work.full():
            tight_loop = False

            metatile = self.work_stack.pop()  # tiles.MetaTile
            if metatile is not None:
                # TODO: move to another thread
                if not self.should_render(metatile):
                    continue

                # self.log_grafana(str(metatile))

                # because we're the only writer, and it's not full, this can't block
                self.new_work.put(metatile)
                self.work_stack.confirm()
                self.went_out += 1
                debug("--> %r", (metatile, ))

                if self.opts.parallel == 'single':
                    self.renderer.single_step()
                    # also, get out of here, so we can clean up
                    # in the next loop
                    break
            else:
                # no more work to do
                tight_loop = True
                break

        while not self.info.empty():
            tight_loop = False

            data = self.info.get()  # type: Tuple[str, Any]
            debug("<-- %s", data)

            self.handle_new_work(data)

        return tight_loop


    def handle_new_work(self, metatile):
        # an empty metatile will be accounted as rendered,
        # but the children can be pruned
        if self.opts.push_children and metatile.z < self.opts.max_zoom:
            # TODO: why reversed?
            for child in reversed(metatile.children()):
                debug("%r: %s, %s", child, child.render, child.is_empty)
                if child.render:
                    self.work_stack.push(child)
                elif child.is_empty:
                    self.tiles_skipped += ( len(child.tiles) *
                                            utils.pyramid_count(child.z, opts.max_zoom) )
                    self.progress(child, format="empty")

        self.tiles_rendered += len(metatile.tiles)
        self.came_back += 1

        self.progress(metatile, *metatile.times(),  format="%8.3f, %8.3f, %8.3f, %8.3f")


    def finish(self):
        if self.opts.parallel != 'single':
            info('stopping threads/procs')
            # signal render threads to exit by sending empty request to queue
            for i in range(self.opts.threads):
                info("%d...", (i + 1))
                self.new_work.put(None)

            while self.went_out > self.came_back:
                debug("sent: %d; returned: %d", self.went_out, self.came_back)
                data = self.info.get()  # type: str, Any
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
    group.add_argument('-T', '--tiles',         dest='tiles',     default= None, nargs='+', metavar='[Z,X,Y|Z/X/Y]',
                       help="Render this list of [meta]tiles.")
    group.add_argument('-c', '--coords',        dest='coords',    default=None, nargs='+',
                       metavar='[Lat,Long|Lat/Long]',
                       help="Render this exact coords as the center of the [meta]tile. Order is LatLong, like in 31˚S, 64°W")
    group.add_argument('-L', '--longlat',        dest='longlat',    default=None, nargs=2,
                       metavar=('LONG', 'LAT'),
                       help='Render this exact coords as the center of the [meta]tile. Order is LongLat as in X,Y')

    parser.add_argument('-n', '--min-zoom',      dest='min_zoom',  default=0, type=int)
    parser.add_argument('-x', '--max-zoom',      dest='max_zoom',  default=18, type=int)

    parser.add_argument('-i', '--input-file',       dest='mapfile',          default='osm.xml',
                        help="MapnikXML format.")
    parser.add_argument('-f', '--format',           dest='format',           default='tiles',
                        choices=('tiles', 'mbtiles', 'mod_tile', 'test', 'svg', 'pdf'))
    parser.add_argument('-F', '--tile-file-format', dest='tile_file_format', default='png',
                        choices=('png', 'jpeg', 'svg', 'pdf'))
    parser.add_argument('-O', '--tile-file-format-options', dest='tile_file_format_options', default='',
                        help='Check https://github.com/mapnik/mapnik/wiki/')
    parser.add_argument('-o', '--output-dir',       dest='tile_dir',         default='tiles/')
    parser.add_argument(      '--filename-pattern', dest='filename_pattern', default=None,
                        help="Pattern may include {base_dir}, {x}, {y} and {z}.")

    # TODO: check it's a power of 2
    parser.add_argument('-m', '--metatile-size', dest='metatile_size', default=1, type=int,
                        help='Must be a power of two.')

    parser.add_argument('-t', '--threads',       dest='threads',   default=utils.NUM_CPUS,
                        type=int)
    parser.add_argument('-p', '--parallel-method', dest='parallel', default='fork',
                        choices=('threads', 'fork', 'single'))
    parser.add_argument(      '--store-thread', dest='store_thread', default=False,
                        action='store_true', help="Have a separate process/thread for storing the tiles.")

    parser.add_argument('-X', '--skip-existing', dest='skip_existing', default=False,
                        action='store_true')
    # TODO: newer than input_file
    parser.add_argument('-N', '--skip-newer',      dest='skip_newer', default=None,
                        type=float, metavar='DAYS')
    parser.add_argument('-M', '--missing-as-new',  dest='missing_as_new', default=False,
                        action='store_true', help="missing tiles in a meta tile count as newer, so we don't re-render metatiles with empty tiles.")
    parser.add_argument('-e', '--empty-color',     dest='empty_color', metavar='[#]RRGGBB', required=True,
                        help='Define the color of empty space (usually sea/ocean color) for empty tile detection.')
    parser.add_argument('-s', '--empty-size',      dest='empty_size', type=int, default=103,
                        help='The byte size of empty tiles.')
    parser.add_argument('-E', '--empty',           dest='empty',     default='skip',
                        choices=('skip', 'link', 'write'))

    parser.add_argument(      '--debug',    dest='debug',    default=False,
                        action='store_true')
    parser.add_argument('-l', '--log-file', dest='log_file', default=None)
    parser.add_argument(      '--dry-run',  dest='dry_run',  default=False,
                        action='store_true')

    parser.add_argument(      '--mapnik-debug',  dest='mapnik_debug',  default=False,
                        action='store_true', help='''Turn on mapnik's debug logs.''')
    parser.add_argument(      '--mapnik-strict', dest='mapnik_strict', default=False,
                        action='store_true', help='''Use Mapnik's strict mode.''')

    # TODO: buffer size (256?)
    opts = parser.parse_args()

    # verboseness
    if opts.debug:
        logging.basicConfig(level=logging.DEBUG, format=long_format)
    else:
        logging.basicConfig(level=logging.INFO, format=short_format)

    if opts.mapnik_debug:
        mapnik.logger.set_severity(mapnik.severity_type.Debug)

    debug(opts)

    ## log outputs
    if opts.log_file is not None:
        root = logging.getLogger()
        file_handler = logging.FileHandler(opts.log_file)

        if opts.debug:
            file_handler.setFormatter(logging.Formatter(long_format))
            file_handler.setLevel(logging.DEBUG)
            # the root logger will be pre-filtering by level
            # so we need to set its level to the lowest possible
            root.setLevel(logging.DEBUG)
        else:
            file_handler.setFormatter(logging.Formatter(short_format))
            file_handler.setLevel(logging.INFO)
            root.setLevel(logging.INFO)

        root.addHandler(file_handler)

    ## tile_dir
    if opts.format == 'tiles' and opts.tile_dir[-1] != '/':
        # we need the trailing /, it's actually a series of BUG s in render_tiles()
        opts.tile_dir += '/'

    opts.tile_dir = os.path.abspath(opts.tile_dir)
    if opts.skip_newer is not None:
        opts.skip_newer = ( datetime.datetime.now() -
                            datetime.timedelta(days=opts.skip_newer) )

    ## bbox
    if opts.bbox_name is not None:
        # pick bbox from bboxes.ini
        atlas = map_utils.Atlas([ opts.bbox_name ])
        opts.bbox = map_utils.BBox(atlas.maps[opts.bbox_name].bbox, opts.max_zoom)
    else:
        opts.bbox = map_utils.BBox([ float(s) for s in opts.bbox.split(',') ], opts.max_zoom)

    ## tile_file_format
    if opts.format == 'mod_tile' and opts.tile_file_format != 'png':
        warning(f"mod_tile format doesnt support '{opts.tile_file_format}'. Forcing 'png'.")
        opts.tile_file_format = 'png'

    ## misc stuff for certain formats
    if opts.format in ('mod_tile', 'test'):
        # mod_tile's tiles are really metatiles, 8x8
        # so we make the tile size 8 times a tile, and the metatile size is divided by 8
        opts.tile_size = 8 * 256

        # normalize values
        if opts.metatile_size < 8:
            opts.metatile_size = 8
        opts.metatile_size //= 8

        if opts.tiles is not None:
            metatiles = []

            for tile_spec in opts.tiles:
                z, x, y = tiles.tile_spec2zxy(tile_spec)

                # normalize
                x //= 8
                y //= 8

                metatile = tiles.MetaTile(z, x, y, opts.metatile_size, opts.tile_size)
                metatiles.append(metatile)

            opts.tiles = metatiles
    else:
        # NOTE: no high res support
        opts.tile_size = 256
        if opts.tiles is not None:
            metatiles = []

            for tile_spec in opts.tiles:
                z, x, y = tiles.tile_spec2zxy(tile_spec)
                metatile = tiles.MetaTile(z, x, y, opts.metatile_size, opts.tile_size)
                metatiles.append(metatile)

            opts.tiles = metatiles

    # TODO: svg is too special?
    if opts.format in ('svg', 'pdf'):
        if opts.coords is None and opts.longlat is None:
            error('SVG/PDF formats only work with --coords or --longlat.')
            sys.exit(1)

        if opts.parallel != 'single':
            warning('SVG/PDF formats. Forcing single thread.')
            opts.parallel = 'single'

        if opts.store_thread:
            warning('SVG/PDF formats. Forcing no store thread.')
            opts.store_thread = False

        if opts.tile_file_format != opts.format:
            warning('SVG/PDF formats. Forcing file format.')
            opts.tile_file_format = opts.format

        # lazy import
        debug('loading cairo for SVG/PDF')
        global cairo
        import cairo

    ## convert coordinates
    if opts.coords is not None or opts.longlat is not None:
        opts.tile_size = 1024

        if opts.coords is not None:
            # input is Lat,Long, but tileproj works with Lon,Lat; convert
            new_coords = []

            for coord in opts.coords:
                data = coord.split('/')

                if len(data) == 3:
                    # it has a zoom level spec too, use that as min_zoom, max_zoom
                    zoom, lat, long = data
                    opts.min_zoom = int(zoom)
                    opts.max_zoom = opts.min_zoom
                else:
                    lat, long = data

                new_coords.append( (float(long), float(lat)) )

            opts.coords = new_coords

        elif opts.longlat is not None:
            # input is Long Lat already
            long, lat = opts.longlat
            opts.coords = [ (float(long), float(lat)) ]

        debug(opts.coords)

        metatiles = []

        for coord in opts.coords:
            for z in range(opts.min_zoom, opts.max_zoom + 1):
                # TODO: maybe move this conversion to PixelTile
                x, y = tiles.tileproj.lon_lat2pixel(coord, z)
                tile = tiles.PixelTile(z, x, y, opts.tile_size)
                metatiles.append(tile)

        opts.tiles = metatiles

    ## parallel + threads
    if opts.threads == 1:
        opts.parallel == 'single'

    # I need this for ... what?
    if opts.parallel == 'single':
        opts.threads = 1
        opts.store_thread = False
    elif opts.parallel == 'fork':
        debug('mp.Process()')
        opts.parallel_factory = multiprocessing.Process
    elif opts.parallel == 'threads':
        debug('th.Thread()')
        opts.parallel_factory = threading.Thread

    ## empty_color
    # TODO: accept other formats
    try:
        # cut the leading #
        if len(opts.empty_color) == 7 and opts.empty_color[0] == '#':
            opts.empty_color = opts.empty_color[1:]

        opts.empty_color = bytes([ int(opts.empty_color[index:index + 2], 16)
                                   for index in (0, 2, 4) ])
    except ValueError:
        parser.print_help()
        sys.exit(1)

    ## more_opts, for tile backends
    opts.more_opts = {}
    if opts.filename_pattern is not None:
        opts.more_opts['filename_pattern'] = opts.filename_pattern

    # semantic opts
    opts.single_tiles = opts.tiles is not None
    opts.push_children = not opts.single_tiles

    # debug(opts)
    info(opts)

    return opts


if __name__  ==  "__main__":
    opts = parse_args()

    master = Master(opts)

    # fixes for locally installed mapnik
    mapnik.register_fonts ('/usr/share/fonts/')
    mapnik.register_plugins ('/home/mdione/local/lib/mapnik/input/')
    info(mapnik.__file__)

    master.render_tiles()
