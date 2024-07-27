#! /usr/bin/env python3

import socket
from  selectors import DefaultSelector as Selector, EVENT_READ, EVENT_WRITE


def main():
    listener = socket.socket()
    listener.bind( ('', 8080) )
    listener.listen(32)

    listener.setblocking(False)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

    selector = Selector()
    selector.register(listener, EVENT_READ)

    clients = set()

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
                        client.close()
                        selector.unregister(client)


if __name__ == '__main__':
    main()
