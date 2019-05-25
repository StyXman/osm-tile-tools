# osm-tile-tools

This repo contains several tools related to tile rendering and serving.

## generate_tiles.py

This tool is a fork of the original script in [OSM's mapnik-style](https://github.com/openstreetmap/mapnik-stylesheets/blob/master/generate_tiles.py).

It has been expanded to handle more situations, including:

* Threaded vs Forking (the latter works better doe to a bug in mapnik).
* Store tiles in several formats and directory schemas:
  * slippy map tiles
  * mod_tile
  * mbtiles
* Render tiles older than a certain date.
* Not storing empty sea tiles.
* Render by bbox, LonLat coords, or bboxes stored in a config file.
* And more!

```
usage: generate_tiles.py [-h]
                         [-b W,S,E,N | -B BBOX_NAME | -T METATILE [METATILE ...]
                         | -c COORDS | -L LONG LAT] [-n MIN_ZOOM]
                         [-x MAX_ZOOM] [-i MAPFILE]
                         [-f {tiles,mbtiles,mod_tile,test}] [-o TILE_DIR]
                         [-m METATILE_SIZE] [-t THREADS]
                         [-p {threads,fork,single}] [--store-thread] [-X]
                         [-N DAYS] [--missing-as-new] [-E {skip,link,write}]
                         [--debug] [-l LOG_FILE] [--dry-run] [--strict]

optional arguments:
-h, --help            show this help message and exit
-b W,S,E,N, --bbox W,S,E,N
-B BBOX_NAME, --bbox-name BBOX_NAME
-T METATILE [METATILE ...], --tiles METATILE [METATILE ...]
                        METATILE can be in the form Z,X,Y or Z/X/Y.
-c COORDS, --coords COORDS
                        COORDS can be in form 'Lat,Lon', ´Lat/Lon'.
-L LONG LAT, --longlat LONG LAT
-n MIN_ZOOM, --min-zoom MIN_ZOOM
-x MAX_ZOOM, --max-zoom MAX_ZOOM
-i MAPFILE, --input-file MAPFILE
                        MapnikXML format.
-f {tiles,mbtiles,mod_tile,test}, --format {tiles,mbtiles,mod_tile,test}
-o TILE_DIR, --output-dir TILE_DIR
-m METATILE_SIZE, --metatile-size METATILE_SIZE
                        Must be a power of two.
-t THREADS, --threads THREADS
-p {threads,fork,single}, --parallel-method {threads,fork,single}
--store-thread        Have a separate process/thread for storing the tiles.
-X, --skip-existing
-N DAYS, --skip-newer DAYS
--missing-as-new      missing tiles in a meta tile count as newer, so we
                        don't re-render metatiles with empty tiles.
-E {skip,link,write}, --empty {skip,link,write}
--debug
-l LOG_FILE, --log-file LOG_FILE
--dry-run
--strict              Use Mapnik's strict mode.
```

## tile_list.py

Returns the list of slippy map tiles for a bbox and max ZL

Example:

    ./tile_list.py 7.419318,46.92836,7.487983,46.997832,10
    0/0/0.png
    1/1/0.png
    2/2/1.png
    3/4/2.png
    4/8/5.png
    5/16/11.png
    6/33/22.png
    7/66/45.png
    8/133/90.png
    9/266/180.png
    10/533/360.png

## tile_server.py

It serves slippy map tiles over http, using several sources than can b either in
slippy map format or MBTiles. Each tile is search on each source until found, so
you can stack several sources like that.

I developed this so I could serve a country size map down to ZL11 plus several
city-and-about maps down to ZL18.

Example:

    ./tile_server.py Argentina.sqlitedb Cordoba.sqlitedb  # OsmAnd MBTiles format

# TODO

The rest.
