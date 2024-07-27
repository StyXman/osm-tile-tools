#! /usr/bin/env python3

import socket
from  selectors import DefaultSelector as Selector, EVENT_READ, EVENT_WRITE


def main():
    listener = socket.socket()
    listener.bind( ('', 8080) )
    listener.listen(32)

    listener.setblocking(False)

    selector = Selector()
    selector.register(listener, EVENT_READ)

    clients = set()

    while True:
        for key, events in selector.select():
            if key.fileobj == listener:
                # new client
                client, addr = listener.accept()
                print(f"connection from {addr}")


if __name__ == '__main__':
    main()
