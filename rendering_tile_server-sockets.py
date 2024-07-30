#! /usr/bin/env python3

from collections import defaultdict, deque
from dataclasses import dataclass
import multiprocessing
import os
import os.path
import random
import re
from  selectors import DefaultSelector as Selector, EVENT_READ, EVENT_WRITE
import socket
import sys
import time

import logging
from logging import debug, info, exception, warning
long_format = "%(asctime)s %(name)16s:%(lineno)-4d (%(funcName)-21s) %(levelname)-8s %(message)s"
short_format = "%(asctime)s %(message)s"

logging.basicConfig(level=logging.DEBUG, format=long_format)

# fake multiprocessing for testing
class RenderThread:
    def __init__(self, opts, input, output):
        self.input = input
        self.output = output

    def render_metatile(self, work):
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

        return self.render_metatile(work)


class Master:
    def __init__(self, opts):
        self.renderers = {}

        # we have several data structures here
        # work_for_metatile maps MetaTiles to Works, so we can:
        # * know if we have it either queued or rendering
        # * find it again so we can add more clients
        self.work_for_metatile = {}
        # work_for_client maps clients to Works, so we can remove the client from the work if needed
        self.work_for_client = {}
        # the Work queue
        self.work_stack = deque(maxlen=4096)
        # the Work being rendered
        self.in_flight = set()

        self.new_work = multiprocessing.Queue(1)
        self.info = multiprocessing.Queue(5*8)

        for i in range(8):
            renderer = RenderThread(None, self.new_work, self.info)
            render_thread = multiprocessing.Process(target=renderer.loop, name=f"Renderer-{i+1:03d}")
            renderer.name = render_thread.name

            render_thread.start()
            self.renderers[i] = render_thread

    def append(self, metatile, client, tile_path):
        if metatile not in self.work_for_metatile:
            debug(f"[Master]: new  work for {metatile!r}: {client}")
            new_work = Work(metatile, [ (client, tile_path) ])

            self.work_stack.append(new_work)
            self.work_for_metatile[metatile] = new_work
            self.work_for_client[client] = new_work
        else:
            old_work = self.work_for_metatile[metatile]
            old_work.clients.append( (client, tile_path) )
            self.work_for_client[client] = old_work
            debug(f"[Master]: more work for {old_work.metatile!r}: {old_work.clients}")

    def remove(self, client_to_remove):
        work = work_for_client[client_to_remove]

        # now, this might seem dangerous, but all these structures are handled on the main thread
        # so there is no danger of race conditions

        # search for the client because we don't have query information
        for client, tile_path in work.clients:
            if client == client_to_remove:
                debug(f"found {client_to_remove} in {work.metatile!r}")
                work.clients.remove( (client, tile_path) )

        # if this work ends without clients, remove it
        if len(work.clients) == 0:
            # no need to remove it from in_flight; all will be handled when the MetaTile has finished being rendered
            # TODO: explain why
            if work not in self.in_flight:
                debug(f"work for {work.metatile!r} empty, removing before it's sent for rendering")
                self.work_stack.remove(work)
                del self.work_for_metatile[work.metatile]
                del self.work_for_client[client_to_remove]

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

            work = self.work_stack.popleft()  # Work

            if work is not None:
                # because we're the only writer, and it's not full, this can't block
                debug('[Master] new_work.put...')
                self.new_work.put(work)
                debug('[Master] ... new_work.put!')
                debug(f"[Master] --> {work.metatile!r}")
                debug(f"[Master] --> {work.clients}")

                # moving from work_stack to in_flight
                self.in_flight.add(work)
            else:
                # no more work to do
                tight_loop = True
                break

        result = []
        while not self.info.empty():
            tight_loop = False

            debug('info.get...')
            work = self.info.get()
            debug('... info.got!')
            debug(f"[Master] <-- {work.metatile!r}")
            debug(f"[Master] <-- {work.clients}")

            # bookkeeping
            self.in_flight.remove(work)
            del self.work_for_metatile[work.metatile]
            for client, _ in work.clients:
                del self.work_for_client[client]

            result.append(work)

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

@dataclass
class Work:
    metatile: MetaTile
    # TODO: maybe a set?
    clients: list[(socket.socket, str)]

    def __eq__(self, other):
        return self.metatile == other.metatile

    def __hash__(self):
        return hash(self.metatile)


def main(root):
    listener = socket.socket()
    # before bind
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

    listener.bind( ('', 8080) )
    listener.listen(32)
    listener.setblocking(False)

    selector = Selector()
    selector.register(listener, EVENT_READ)

    clients = set()
    responses = defaultdict(list)
    queries_clients = DoubleDict()

    # canonicalize
    root = os.path.abspath(root)

    # b'GET /12/2111/1500.png HTTP/1.1\r\nHost: ioniq:8080\r\nConnection: Keep-Alive\r\nAccept-Encoding: gzip\r\nUser-Agent: okhttp/3.12.2\r\n\r\n'
    # but we only care about the first line, so
    # GET /12/2111/1500.png HTTP/1.1
    request_re = re.compile(r'(?P<method>[A-Z]+) (?P<url>.*) (?P<version>.*)')

    master = Master(None)

    while True:
        for key, events in selector.select(0.1):
            ready_socket = key.fileobj

            if ready_socket == listener:
                # new client
                client, addr = listener.accept()
                debug(f"connection from {addr}")

                clients.add(client)
                selector.register(client, EVENT_READ | EVENT_WRITE)

            elif ready_socket in clients:
                client = ready_socket

                if events & EVENT_READ:
                    data = client.recv(4096)
                    debug(f"read from {client.getpeername()}: {data}")

                    if len(data) == 0:
                        # remove any trailing data
                        if client in responses:
                            del responses[client]

                        # clean up trailing queries from the work_stack
                        query = queries_clients.get(client, None)
                        if query is not None:
                            try:
                                master.work_stack.remove(query)
                            except ValueError:
                                # already being rendered, ignore
                                pass

                            debug(f"client {client.getpeername()} disconnected, was waiting for {query}")
                        else:
                            debug(f"client {client.getpeername()} disconnected, didn't made any query yet.")

                        responses[client] = []
                    else:
                        # splitlines() already handles any type of separators
                        lines = data.decode().splitlines()
                        request_line = lines[0]
                        match = request_re.match(request_line)

                        if match is None:
                            responses[client] = [ b'HTTP/1.1 400 KO\r\n\r\n' ]

                        if match['method'] != 'GET':
                            responses[client] = [ b'HTTP/1.1 405 only GETs\r\n\r\n' ]

                        path = match['url']

                        # TODO: similar code is in tile_server. try to refactor
                        try:
                            # _ gets '' because self.path is absolute
                            _, z, x, y_ext = path.split('/')
                        except ValueError:
                            responses[client] = [ f"HTTP/1.1 400 bad tile spec {self.path}\r\n\r\n".encode() ]
                        else:
                            # TODO: make sure ext matches the file type we return
                            y, ext = os.path.splitext(y_ext)

                            # o.p.join() considers path to be absolute, so it ignores root
                            tile_path = os.path.join(root, z, x, y_ext)
                            master.work_stack.append(tile_path)
                            queries_clients[client] = tile_path

                if events & EVENT_WRITE:
                    if client in responses:
                        for data in responses[client]:
                            if len(data) > 0:
                                debug(f"serving {data} to {client.getpeername()}")
                                if isinstance(data, bytes):
                                    sent = client.send(data)
                                    # TODO
                                    assert sent == len(data), f"E: Could not send all {data} to {client.getpeername()}"
                                else:
                                    client.sendfile(open(data, 'br'))

                        del responses[client]

                        # no keep alive support
                        debug(f"closing {client.getpeername()}")
                        client.close()

                        # bookkeeping
                        selector.unregister(client)
                        clients.remove(client)
                        del queries_clients[client]

        # advance the queues
        _, tile_paths = master.single_step()

        for tile_path in tile_paths:
            client = queries_clients[tile_path]

            try:
                # this could be considered 'blocking', but if the fs is slow, we have other problems
                file_attrs = os.stat(tile_path)
            except FileNotFoundError:
                responses[client] = [ f"HTTP/1.1 404 not here {tile_path}\r\n\r\n".encode() ]
            else:
                responses[client].append(b'HTTP/1.1 200 OK\r\n')
                responses[client].append(b'Content-Type: image/png\r\n')
                responses[client].append(f"Content-Length: {file_attrs.st_size}\r\n\r\n".encode())
                responses[client].append(tile_path)


if __name__ == '__main__':
    main(sys.argv[1])
