#! /usr/bin/python3

# set -e
# no equivalent yet

import sys
import sh
import re
import math
from file_test import _f
import time
import os

pbf_file= sys.argv[1]
extent= sh.grep (sh.osmpbf_outline (pbf_file, _tty_out=False, _ok_code=1), 'bbox')

#     bbox: 9.5267800,46.3685100,17.1627300,49.0240300
try:
    west, south, east, north= [ float (x) for x in re.split ("[:,]", str (extent))[1:] ]
except (ValueError, AttributeError) as e:
    print ("cannot find the extent of %s [%s]; bailing out" % (pbf_file, e))
    sys.exit (1)

print (west, south, east, north)

# we don't need the +1 on the left right limit, as we're already using ceiling()
# but the tiles count from the south and west
for lat in range (math.floor (south), math.ceil (north)):
    for lon in range (math.floor (west), math.ceil (east)):
        if lat<0:
            lat_template= "S%02d"
        else:
            lat_template= "N%02d"

        if lon<0:
            lon_template= "W%03d"
        else:
            lon_template= "E%03d"

        zip_file= "%s%s.hgt.zip" % (lat_template % abs (lat), lon_template % abs (lon))

        if not _f (zip_file):
            try:
                url= "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/South_America/%s" % zip_file
                reason= sh.wget (url, _out=sys.stdout)

                print ("Got %s" % zip_file)
            except sh.ErrorReturnCode as e:
                print ("could not get %s; skipping" % url)

        if _f(zip_file):
            sh.unzip ("-u %s" % zip_file)
            os.unlink (zip_file)

        time.sleep (1)
