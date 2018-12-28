#! /usr/bin/env python3

import sys
import os.path

import map_utils

sector = sys.argv[1]

a = map_utils.Atlas([sector])
m = a.maps[sector]
be = map_utils.MBTilesBackend(sector, m.bbox)

print('INSERTING TILES')
for z in range (m.max_z+1):
    for x in m.iterate_x (z):
        for y in m.iterate_y (z):
            try:
                data = open(os.path.join('Elevation', str (z), str (x), "%d.png" % y),
                            'rb').read()
            except FileNotFoundError:
                pass
            else:
                be.store_raw(z, x, y, data)

        be.commit()
