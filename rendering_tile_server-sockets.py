#! /usr/bin/env python3

from collections import defaultdict, deque
import multiprocessing
import os
import os.path
import random
import re
from  selectors import DefaultSelector as Selector, EVENT_READ, EVENT_WRITE
import socket
import sys
import time
import traceback

from generate_tiles import RenderThread, StormBringer
import map_utils
from tiles import Tile, MetaTile
import utils

import logging
from logging import debug, info, exception, warning
long_format = "%(asctime)s %(name)16s:%(lineno)-4d (%(funcName)-21s) %(levelname)-8s %(message)s"
short_format = "%(asctime)s %(message)s"

logging.basicConfig(level=logging.DEBUG, format=long_format)

# fake multiprocessing for testing
class FakeRenderThread:
    def __init__(self, opts, input, output):
        self.input = input
        self.output = output

    def render(self, work):
        seconds = random.randint(3, 75)
        debug(f"[{self.name}]    {work.metatile}: sleeping for {seconds}...")
        time.sleep(seconds)
        debug(f"[{self.name}]    {work.metatile}: ... {seconds} seconds!")
        self.output.put(work)

        return True

    def load_map(self):
        pass

    def loop(self):
        debug(f"[{self.name}] loop")
        while self.single_step():
            pass

        debug(f"[{self.name}] done")

    def single_step(self):
        work = self.input.get()
        debug(f"[{self.name}] step")
        if work is None:
            debug(f"[{self.name}] bye!")
            # it's the end; send the storage thread a message and finish
            self.output.put(None)
            return False

        return self.render(work)


class Master:
    def __init__(self, opts):
        self.renderers = {}

        # we have several data structures here
        # clients_for_metatile maps MetaTiles to Clients, so we can:
        # * know if we have it either queued or rendering
        # * find it again so we can add more clients
        self.clients_for_metatile = defaultdict(set)
        # metatile_for_client maps Clients to MetaTiles, so we can remove the Client from the MT's client list
        self.metatile_for_client = {}
        # the MetaTile queue
        self.work_stack = deque(maxlen=4096)
        # the MetaTile being rendered
        self.in_flight = set()

        self.new_work = multiprocessing.Queue(1)
        self.store_queue = utils.SimpleQueue(5*opts.threads)
        self.info = multiprocessing.Queue(5*8)

        self.backend = map_utils.DiskBackend(opts.tile_dir)
        self.store_thread = StormBringer(opts, self.backend, self.store_queue, self.info)
        self.store_thread.name = 'store-embedded'

        for i in range(8):
            renderer = RenderThread(opts, self.new_work, self.store_queue)
            render_thread = multiprocessing.Process(target=renderer.loop, name=f"Renderer-{i+1:03d}")
            renderer.name = render_thread.name
            renderer.store_thread = self.store_thread

            render_thread.start()
            self.renderers[i] = render_thread

    def append(self, metatile, client):
        if metatile not in self.clients_for_metatile:
            debug(f"[Master]: first Client for {metatile!r}: {client}")

            self.work_stack.append(metatile)
            self.clients_for_metatile[metatile].add(client)
            self.metatile_for_client[client] = metatile
        else:
            clients = self.clients_for_metatile[metatile]
            clients.add(client)
            self.metatile_for_client[client] = metatile
            debug(f"[Master]: new Client for {metatile!r}: {clients}")

    def remove(self, client_to_remove):
        metatile = self.metatile_for_client[client_to_remove]

        # now, this might seem dangerous, but all these structures are handled on the main thread
        # so there is no danger of race conditions
        clients = self.clients_for_metatile[metatile]
        clients.remove(client)

        # if this metatile ends without clients, remove it
        if len(clients) == 0:
            # no need to remove it from in_flight; all will be handled when the MetaTile has finished being rendered
            # TODO: explain why
            if metatile not in self.in_flight:
                debug(f"clients for {metatile!r} empty, removing before it's sent for rendering")
                self.work_stack.remove(metatile)
                del self.clients_for_metatile[metatile]
                del self.metatile_for_client[client_to_remove]

    def render_tiles(self):
        try:
            self.loop([])
        except KeyboardInterrupt:
            print('C-c detected, exiting')
        except Exception as e:
            print(f"Unknown exception {e}")
        finally:
            print('finishing!')
            self.finish()

    def loop(self, initial_metatiles):
        while True:
            self.single_step()

    def single_step(self):
        # TODO: similar to generate_tiles'

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
        while not self.new_work.full() and len(self.work_stack) > 0:
            tight_loop = False

            metatile = self.work_stack.popleft()  # tiles.MetaTile

            if metatile is not None:
                # because we're the only writer, and it's not full, this can't block
                debug('[Master] new_work.put...')
                self.new_work.put(metatile)
                debug('[Master] ... new_work.put!')
                debug(f"[Master] --> {metatile!r}")
                debug(f"[Master] --> {clients}")

                # moving from work_stack to in_flight
                self.in_flight.add(metatile)
            else:
                # no more work to do
                tight_loop = True
                break

        result = []
        while not self.info.empty():
            tight_loop = False

            debug('info.get...')
            metatile = self.info.get()
            clients = self.clients_for_metatile[metatile]

            debug('... info.got!')
            debug(f"[Master] <-- {metatile!r}")
            debug(f"[Master] <-- {clients=}")

            # bookkeeping
            self.in_flight.remove(metatile)
            del self.clients_for_metatile[metatile]
            for client in clients:
                del self.metatile_for_client[client]

            result.append(metatile)

        return tight_loop, result

    def finish(self):
        for i in range(8):
            self.new_work.put(None)

        while not self.info.empty():
            data = self.info.get()
            debug(f"[Master] <-- {data}")

        self.new_work.join()
        for i in range(8):
            self.renderers[i].join()
        debug('finished')


class DoubleDict:
    def __init__(self):
        self.forward = {}
        self.backward = {}

    def __getitem__(self, key):
        if key in self.forward:
            return self.forward[key]

        return self.backward[key]

    def __setitem__(self, key, value):
        self.forward[key] = value
        self.backward[value] = key

    def __delitem__(self, key):
        if key not in self.forward and key not in self.backward:
            raise KeyError

        if key in self.forward:
            value = self.forward.pop(key)
        else:
            value = self.backward.pop(key)

        if value in self.forward:
            del self.forward[value]
        else:
            del self.backward[value]

    def __contains__(self, key):
        return key in self.forward or key in self.backward

    def get(self, key, default=None):
        if key in self.forward:
            value = self.forward.pop(key)
        elif key in self.backward:
            value = self.backward.pop(key)
        else:
            value = default

        return value


class Client:
    def __init__(self, socket):
        self.socket = socket

        # to support short reads we will be using a buffer and an offset that will point to the first free byte
        self.read_buffer = memoryview(bytearray(4096))  # we really don't need much, since requests are quite small
        self.read_buffer_offset = 0
        self.request_read = False

        self.write_data = []
        self.write_file = None

        self.tile_path = None

    def recv(self):
        # if the last time we finished reading the request, we have to start from 0
        if self.request_read:
            self.request_read = False
            self.read_buffer_offset = 0

        read = self.socket.recv_into(self.read_buffer[self.read_buffer_offset:])  # the size is automatic
        if read > 0:
            self.read_buffer_offset += read

        # ugh that bytes(), I hope it's cheap
        if b'\r\n\r\n' in bytes(self.read_buffer[:self.read_buffer_offset]):
            self.request_read = True

        return self.read_buffer[:self.read_buffer_offset]

    def send(self, data):
        if isinstance(data, bytes):
            # textual data
            self.write_data.append(data)
        else:
            self.write_file = data

    def flush(self):
        for data in self.write_data:
            sent = self.socket.send(data)
            # TODO implement handling of short writes
            assert sent == len(data)

        if self.write_file is not None:
            self.socket.sendfile(open(self.write_file, 'br'))

    def close(self):
        self.socket.close()

    def fileno(self):
        return self.socket.fileno()

    def getpeername(self):
        return self.socket.getpeername()

    def __hash__(self):
        return hash(self.socket)


class Server:
    def __init__(self, opts):
        self.opts = opts

        self.listener = socket.socket()
        # before bind
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

        self.listener.bind( ('', 8080) )
        self.listener.listen(32)
        self.listener.setblocking(False)

        self.selector = Selector()
        self.selector.register(self.listener, EVENT_READ)

        self.clients = set()
        self.queries_clients = DoubleDict()
        self.client_for_peer = {}

        # this looks like dupe'd from Master, but they have slightly different life cycles
        self.clients_for_metatile = defaultdict(set)

        # canonicalize
        # root = os.path.abspath(root)

        # b'GET /12/2111/1500.png HTTP/1.1\r\nHost: ioniq:8080\r\nConnection: Keep-Alive\r\nAccept-Encoding: gzip\r\nUser-Agent: okhttp/3.12.2\r\n\r\n'
        # but we only care about the first line, so
        # GET /12/2111/1500.png HTTP/1.1
        self.request_re = re.compile(r'(?P<method>[A-Z]+) (?P<url>.*) (?P<version>.*)')

        self.master = Master(self.opts)

    def accept(self):
        # new client
        # debug('accept..')
        client_socket, addr = self.listener.accept()
        # debug('...ed!')
        debug(f"connection from {addr}")

        client = Client(client_socket)

        self.clients.add(client)
        self.client_for_peer[client.getpeername()] = client
        self.selector.register(client, EVENT_READ)

    def client_read(self, client):
        data = bytes(client.recv())
        debug(f"read from {client.getpeername()}: {data}")

        if len(data) == 0:
            debug(f"client {client.getpeername()} disconnected")

            # clean up trailing queries from the work_stack
            query = self.queries_clients.get(client, None)
            if query is not None:
                try:
                    self.master.work_stack.remove(query)
                except ValueError:
                    # already being rendered, ignore
                    pass

                # debug(f"client {client.getpeername()} disconnected, was waiting for {query}")
            else:
                # debug(f"client {client.getpeername()} disconnected, didn't made any query yet.")
                pass

            # TODO:
            # self.responses[client] = []

            # now we need to wait for client to be ready to write
            self.selector.unregister(client)
            self.selector.register(client, EVENT_WRITE)
        elif client.request_read:
            # we finish reading from this one for now
            self.selector.unregister(client)

            # splitlines() already handles any type of separators
            lines = data.decode().splitlines()
            request_line = lines[0]
            match = self.request_re.match(request_line)

            if match is None:
                client.send(b'HTTP/1.1 400 KO\r\n\r\n')
            else:
                if match['method'] != 'GET':
                    client.send(b'HTTP/1.1 405 only GETs\r\n\r\n')
                else:
                    path = match['url']

                    # TODO: similar code is in tile_server. try to refactor
                    try:
                        # _ gets '' because path is absolute
                        _, z, x, y_ext = path.split('/')
                    except ValueError:
                        client.send(f"HTTP/1.1 400 bad tile spec {path}\r\n\r\n".encode())
                    else:
                        # TODO: make sure ext matches the file type we return
                        y, ext = os.path.splitext(y_ext)

                        # o.p.join() considers path to be absolute, so it ignores root
                        tile_path = os.path.join(self.opts.tile_dir, z, x, y_ext)

                        # try to send tyhe tile first, but do not send 404s
                        if not self.answer(client, tile_path, send_404=False):
                            tile = Tile(*[ int(coord) for coord in (z, x, y) ])
                            metatile = MetaTile.from_tile(tile, 8)
                            debug(f"{client.getpeername()}: {metatile!r}")

                            client.metatile = metatile
                            client.tile_path = tile_path

                            self.clients_for_metatile[metatile].add(client)
                            self.master.append(metatile, client.getpeername())
                            self.queries_clients[client] = tile_path
        else:
            debug(f"short read from {client.getpeername()}")

    def client_write(self, client):
        client.flush()
        # BUG: no keep alive support
        debug(f"closing {client.getpeername()}")
        client.close()

        # bookkeeping
        self.selector.unregister(client)
        self.clients.remove(client)
        if client in self.queries_clients:
            del self.queries_clients[client]

    def loop(self):
        while True:
            try:
                # debug(f"select... [{len(self.master.work_stack)=}; {self.master.new_work.qsize()=}; {self.master.store_queue.qsize()=}; {self.master.info.qsize()=}]")
                for key, events in self.selector.select(1):
                    # debug('...ed!')
                    ready_socket = key.fileobj

                    if ready_socket == self.listener:
                        self.accept()
                    elif ready_socket in self.clients:
                        client = ready_socket

                        if events & EVENT_READ:
                            self.client_read(client)

                        if events & EVENT_WRITE:
                            self.client_write(client)

                # advance the queues
                _, jobs = self.master.single_step()

                for metatile in jobs:
                    debug(f"{metatile=}")
                    # BUG: ugh, shouldn't be touching master's internals like this
                    clients = self.clients_for_metatile[metatile]
                    debug(f"{clients=}")

                    for client in clients:
                        self.answer(client, client.tile_path)

                    # bookkeeping
                    del self.clients_for_metatile[metatile]
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    raise
                else:
                    traceback.print_exc()

    def answer(self, client, tile_path, send_404=True):
        debug(f"answering {client.getpeername()} for {tile_path} ")
        try:
            # this could be considered 'blocking', but if the fs is slow, we have other problems
            debug(f"find me {tile_path}...")
            file_attrs = os.stat(tile_path)
            debug('... stat!')
        except FileNotFoundError:
            if send_404:
                debug(f"not found {tile_path}...")
                client.send(f"HTTP/1.1 404 not here {tile_path}\r\n\r\n".encode())

            return False
        else:
            debug(f"found {tile_path} for {client.getpeername()}")
            client.send(b'HTTP/1.1 200 OK\r\n')
            client.send(b'Content-Type: image/png\r\n')
            client.send(f"Content-Length: {file_attrs.st_size}\r\n\r\n".encode())
            client.send(tile_path)

            # now we need to wait for client to be ready to write
            self.selector.register(client, EVENT_WRITE)

        return True


class Options:
    pass


def main(root):
    opts = Options()

    # alphabetical order
    opts.bbox = None
    opts.coords = None
    opts.dry_run = False
    opts.empty = 'skip'
    opts.empty_color = '#aad3df'
    opts.empty_size = 103
    opts.format = 'tiles'  # TODO?
    opts.mapfile = 'Elevation.xml'
    opts.mapnik_strict = False
    opts.max_zoom = 21  # deep enough
    opts.metatile_size = 8
    opts.more_opts = {}
    opts.parallel = 'fork'
    opts.parallel_factory = None  # TODO
    opts.single_tiles = False
    opts.store_thread = False
    opts.threads = 8  # TODO
    # TODO:
    # opts.tile_dir = app.root_dir
    opts.tile_dir = root
    opts.tile_file_format = 'png'
    opts.tile_file_format_options = ''
    # TODO: no support for hi-res tiles (512)
    opts.tile_size = 256

    server = Server(opts)
    server.loop()


if __name__ == '__main__':
    main(sys.argv[1])
