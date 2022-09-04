#! /usr/bin/env python3

import sys
import os.path

import map_utils

sector = sys.argv[1]

atlas = map_utils.Atlas([sector])
map = atlas.maps[sector]
backend = map_utils.MBTilesBackend(sector, map.bbox)

# backend.init()

print('INSERTING TILES')
for z in range(map.max_z + 1):
    for x in map.iterate_x(z):
        for y in map.iterate_y(z):
            try:
                data = open(os.path.join('Elevation', str(z), str(x), "%d.png" % y),
                            'rb').read()
            except FileNotFoundError:
                pass
            else:
                backend.store_raw(z, x, y, data)

        backend.commit()
