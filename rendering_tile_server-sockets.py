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

    def render_metatile(self, metatile):
        seconds = random.randint(3, 90)
        debug(f"[{self.name}]    {metatile}: sleeping for {seconds}...")
        time.sleep(seconds)
        debug(f"[{self.name}]    {metatile}: ... {seconds} seconds!")
        self.output.put(metatile)

        return True

    def load_map(self):
        pass

    def loop(self):
        debug(f"[{self.name}] loop")
        while self.single_step():
            pass

        debug(f"[{self.name}] done")

    def single_step(self):
        metatile = self.input.get()
        debug(f"[{self.name}] step")
        if metatile is None:
            debug(f"[{self.name}] bye!")
            # it's the end; send the storage thread a message and finish
            self.output.put(None)
            return False

        return self.render_metatile(metatile)


class Master:
    def __init__(self, opts):
        self.renderers = {}

        self.work_stack = deque(maxlen=4096)
        self.new_work = multiprocessing.Queue(1)
        # self.store_queue = SimpleQueue(1)
        self.info = multiprocessing.Queue(5*8)

        for i in range(8):
            # renderer = RenderThread(None, self.new_work, self.store_queue)
            renderer = RenderThread(None, self.new_work, self.info)
            render_thread = multiprocessing.Process(target=renderer.loop, name=f"Renderer-{i+1:03d}")
            renderer.name = render_thread.name

            render_thread.start()
            self.renderers[i] = render_thread

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

            metatile = self.work_stack.popleft()  # map_utils.MetaTile
            if metatile is not None:
                # because we're the only writer, and it's not full, this can't block
                debug('[Master] new_work.put...')
                self.new_work.put(metatile)
                debug('[Master] ... new_work.put!')
                debug(f"[Master] --> {metatile}")
            else:
                # no more work to do
                tight_loop = True
                break

        return tight_loop

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
                        query = queries_clients[client]
                        try:
                            master.work_stack.remove(query)
                        except ValueError:
                            # already being rendered, ignore
                            pass

                        debug(f"client {client.getpeername()} disconnected, was waiting for {query}")

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
        master.single_step()

        while not master.info.empty():
            debug('info.get...')
            data = master.info.get()
            debug('... info.got!')
            debug(f"[main] <-- {data}")

            tile_path = data
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
