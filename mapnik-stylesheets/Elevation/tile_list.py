#! /usr/bin/python2

import sys
from math import pi,cos,sin,log,exp,atan

# shamelessly taken from generate_tiles.py
DEG_TO_RAD = pi/180
RAD_TO_DEG = 180/pi

def minmax (a,b,c):
    a = max(a,b)
    a = min(a,c)
    return a


class GoogleProjection:
    def __init__(self,levels=18):
        self.Bc = []
        self.Cc = []
        self.zc = []
        self.Ac = []
        c = 256
        for d in range(0,levels):
            e = c/2;
            self.Bc.append(c/360.0)
            self.Cc.append(c/(2 * pi))
            self.zc.append((e,e))
            self.Ac.append(c)
            c *= 2

    def fromLLtoPixel(self,ll,zoom):
         d = self.zc[zoom]
         e = round(d[0] + ll[0] * self.Bc[zoom])
         f = minmax(sin(DEG_TO_RAD * ll[1]),-0.9999,0.9999)
         g = round(d[1] + 0.5*log((1+f)/(1-f))*-self.Cc[zoom])
         return (e,g)

    def fromPixelToLL(self,px,zoom):
         e = self.zc[zoom]
         f = (px[0] - e[0])/self.Bc[zoom]
         g = (px[1] - e[1])/-self.Cc[zoom]
         h = RAD_TO_DEG * ( 2 * atan(exp(g)) - 0.5 * pi)
         return (f,h)

bbox= [ float (x) for x in sys.argv[1].split (',') ]

minZoom= 0
maxZoom= int (bbox.pop ())

gprj = GoogleProjection(maxZoom+1)

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
