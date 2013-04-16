#! /bin/bash

export MAPNIK_TILE_DIR=tiles
export MAPNIK_MAP_FILE=tilemill/project/osm-tilemill/mapnik.xml

python mapnik-stylesheets/generate_tiles.py "$@"
