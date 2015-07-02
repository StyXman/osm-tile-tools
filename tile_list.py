#! /usr/bin/python2

import sys

import map_utils

bbox= [ float (x) for x in sys.argv[1].split (',') ]

minZoom= 0
maxZoom= int (bbox.pop ())

gprj = map_utils.GoogleProjection(maxZoom+1)

# print bbox, maxZoom

ll0 = (bbox[0],bbox[3])
ll1 = (bbox[2],bbox[1])

image_size=256.0

for z in range(minZoom,maxZoom + 1):
    px0 = gprj.fromLLtoPixel(ll0,z)
    px1 = gprj.fromLLtoPixel(ll1,z)

    for x in range(int(px0[0]/image_size),int(px1[0]/image_size)+1):
        # Validate x co-ordinate
        if (x < 0) or (x >= 2**z):
            continue

        for y in range(int(px0[1]/image_size),int(px1[1]/image_size)+1):
            # Validate x co-ordinate
            if (y < 0) or (y >= 2**z):
                continue

            print "%d/%d/%d.png" % (z, x, y)
