#! /usr/bin/python3

import sys
import os.path
from PIL import Image

# Mod_tile / renderd store the rendered tiles
# in "meta tiles" in a special hashed directory structure. These combine
# 8x8 actual tiles into a single metatile file. The metatiles are stored
# in the following directory structure:

# /[base_dir]/[TileSetName]/[Z]/[xxxxyyyy]/[xxxxyyyy]/[xxxxyyyy]/[xxxxyyyy]/[xxxxyyyy].png

# Where base_dir is a configurable base path for all tiles. TileSetName
# is the name of the style sheet rendered. Z is the zoom level.
# [xxxxyyyy] is an 8 bit number, with the first 4 bits taken from the x
# coordinate and the second 4 bits taken from the y coordinate. This
# attempts to cluster 16x16 square of tiles together into a single sub
# directory for more efficient access patterns.

#for (i=0; i<5; i++) {
    #hash[i] = ((x & 0x0f) << 4) | (y & 0x0f);
    #x >>= 4;
    #y >>= 4;
#}
def xyz_to_cache (x, y, z):
    h = []

    for i in range(5):
        h.append( ((x & 0x0f) << 4) | (y & 0x0f) )
        x >>= 4
        y >>= 4

    return h


def generate_meta(tileset, col, row, z):
    if z in (0, 1, 2):
        tiles_in_meta = 1 << z
    else:
        tiles_in_meta = 8

    tiles = []
    tile_count = 0

    for x in range(col, col + tiles_in_meta):
        for y in range(row, row + tiles_in_meta):
            tile_file = os.path.join (tileset, str(z), str(x), "%d.png" % y)
            if os.path.exists(tile_file):
                tiles.append(tile_file)
                tile_count += 1
            else:
                tiles.append('sea.png')

    if tile_count>0:
        # do not generate if it's all sea
        # TODO: how to handle this on mod_tile?
        dst = Image.new ('RGB', (256*tiles_in_meta, 256*tiles_in_meta))

        for index, tile in enumerate(tiles):
            src = Image.open(tile)

            x = index // tiles_in_meta
            y = index %  tiles_in_meta


            dst.paste(src, (x*256, y*256))

        crumbs = xyz_to_cache(col, row, z)
        dst_path = os.path.join('/var/lib/mod_tile', tileset.lower(), str(z),
                                *[ str (c) for c in crumbs ])+'.png'

        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        print (z, col, row, dst_path)
        dst.save(dst_path)


tileset = sys.argv[1]
# cache_dir = '/var/cache/mod_tile/%s' % tile_dir.lower()

# TODO: read bboxes
for z in range(19):
    if z in (0, 1, 2):
        mx = 1
    else:
        mx = 1 << (z-3)
    for col in range(mx):
        for row in range(mx):
            generate_meta(tileset, col*8, row*8, z)
