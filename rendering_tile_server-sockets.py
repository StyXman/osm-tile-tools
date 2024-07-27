#! /usr/bin/env python3

from collections import defaultdict
import re
from  selectors import DefaultSelector as Selector, EVENT_READ, EVENT_WRITE
import socket


def main():
    listener = socket.socket()
    listener.bind( ('', 8080) )
    listener.listen(32)

    listener.setblocking(False)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

    selector = Selector()
    selector.register(listener, EVENT_READ)

    clients = set()
    responses = defaultdict(list)

    # b'GET /12/2111/1500.png HTTP/1.1\r\nHost: ioniq:8080\r\nConnection: Keep-Alive\r\nAccept-Encoding: gzip\r\nUser-Agent: okhttp/3.12.2\r\n\r\n'
    # but we only care about the first line, so
    # GET /12/2111/1500.png HTTP/1.1
    request_re = re.compile(r'(?P<method>[A-Z]+) (?P<url>.*) (?P<version>.*)')

    while True:
        for key, events in selector.select():
            ready_socket = key.fileobj

            if ready_socket == listener:
                # new client
                client, addr = listener.accept()
                print(f"connection from {addr}")

                clients.add(client)
                selector.register(client, EVENT_READ | EVENT_WRITE)

            elif ready_socket in clients:
                client = ready_socket

                if events & EVENT_READ:
                    data = client.recv(4096)
                    print(f"read from {client.getpeername()}: {data}")

                    if len(data) == 0:
                        print(f"client {client.getpeername()} disconnected!")
                        # remove any trailing data
                        if client in responses:
                            del responses[client]

                        responses[client] = []
                    else:
                        # splitlines() already handles any type of separators
                        lines = data.decode().splitlines()
                        request_line = lines[0]
                        match = request_re.match(request_line)

                        if match is None or match['method'] != 'GET':
                            responses[client] = [ b'HTTP/1.1 405 only GETs\r\n\r\n' ]

                if events & EVENT_WRITE:
                    if client in responses:
                        for data in responses[client]:
                            if len(data) > 0:
                                print(f"serving {data} to {client.getpeername()}")
                                    client.send(data)

                        del responses[client]

                        # no keep alive support
                        print(f"closing {client.getpeername()}")
                        client.close()
                        selector.unregister(client)


if __name__ == '__main__':
    main()
