#! /usr/bin/python3

# set -e
# no equivalent yet

import sys
from sh import grep, osmpbf_outline, unzip, ErrorReturnCode
import re
import math
from file_test import _f
import time
import os
import urllib.request
import urllib.error

pbf_file= sys.argv[1]
extent= grep (osmpbf_outline (pbf_file, _tty_out=False, _ok_code=1), 'bbox')

#     bbox: 9.5267800,46.3685100,17.1627300,49.0240300
try:
    west, south, east, north= [ float (x) for x in re.split ("[:,]", str (extent))[1:] ]
except (ValueError, AttributeError) as e:
    print ("cannot find the extent of %s [%s]; bailing out" % (pbf_file, e))
    sys.exit (1)

print (west, south, east, north)

# we have 5x5 degrees squares
#  1, 1 for -180,+59,-179,+60
# 13,37 for    0,  0,  +1, +1
# 24,72 for +179,-60,+180,-59

srtm_v41_w= math.floor (west/5)+37
srtm_v41_s= math.floor (-south/5)+13
srtm_v41_e= math.floor (east/5)+37
srtm_v41_n= math.floor (-north/5)+13

print (srtm_v41_w, srtm_v41_s, srtm_v41_e, srtm_v41_n)

os.chdir ('../height')

# +1 so they're proper bounds for range
for lat in range (srtm_v41_n, srtm_v41_s+1):
    for lon in range (srtm_v41_w, srtm_v41_e+1):
        zip_file= "srtm_%02d_%02d.zip" % (lon, lat)

        if not _f ("srtm_%02d_%02d.hgt" % (lon, lat)):
            url= "http://srtm.csi.cgiar.org/SRT-ZIP/SRTM_V41/SRTM_Data_GeoTiff/%s" % zip_file
            try:
                print ("Getting %s ... " % zip_file, end='', flush=True)
                urllib.request.urlretrieve (url, zip_file)
                print ("done!")
            except urllib.error.HTTPError as e:
                print (e)
            else:
                try:
                    # unzip (zip_file)
                    # os.unlink (zip_file)
                    pass
                except ErrorReturnCode as e:
                    print ("unzipping %s failed; keeping..." % zip_file)

        time.sleep (1)
