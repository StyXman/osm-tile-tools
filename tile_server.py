#! /usr/bin/env python3

from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys
import re
import os.path
import os
import stat
from http import HTTPStatus

import map_utils


class TileServer(SimpleHTTPRequestHandler):
    def __init__(self, request, client, server, atlas):
        self.atlas = atlas
        super().__init__(request, client, server)


    def do_GET(self):
        try:
            _, z, x, y_ext = self.path.split('/')
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND, 'Tile not found.')
        else:
            y, ext = os.path.splitext(y_ext)

            tile = map_utils.Tile(*[ int(i) for i in (z, x, y) ])

            # TODO: implement 'depth first'
            for map in self.atlas.values():
                if map.fetch(tile):
                    break

            if tile.data is not None:
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', len(tile.data))
                self.end_headers()
                # TODO; use sendfile
                self.wfile.write(tile.data)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, 'Tile not found.')


def main():
    maps = sys.argv[1:]
    atlas = {}

    # splitext() returns the leading dot
    mbt_exts = re.compile(r'\.(mbt|mbtiles|sqlite|sqlitedb)')

    for map in maps:
        basename, ext = os.path.splitext(map)

        if mbt_exts.match(ext) is not None:
            atlas[basename] = map_utils.MBTilesBackend(basename, ext)

        elif stat.S_ISDIR(os.stat(map).st_mode):
            atlas[basename] = map_utils.DiskBackend(map)

    # TODO: use aio
    server = HTTPServer(('', 4847), lambda *a: TileServer(*a, atlas))

    server.serve_forever()


if __name__ == '__main__':
    main()
