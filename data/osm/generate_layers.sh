#! /bin/bash

set -e

region=$1

# Extent: (9.499995, 46.301027) - (17.212637, 49.067789)

extent_file="${region}/extent.txt"
ogrinfo -al -so ${region}/roads.shp | grep "Extent" > $extent_file
west=$(cat $extent_file | awk 'BEGIN { FS= "[\\(\\), ]" } { print $3 }')
south=$(cat $extent_file | awk 'BEGIN { FS= "[\\(\\), ]" } { print $5 }')
east=$(cat $extent_file | awk 'BEGIN { FS= "[\\(\\), ]" } { print $9 }')
north=$(cat $extent_file | awk 'BEGIN { FS= "[\\(\\), ]" } { print $11 }')

for layer in roads waterways points natural places railways; do
(
cat << EOS
    {
      "geometry": "linestring",
      "extent": [
        $west,
        $south,
        $east,
        $north
      ],
      "id": "${layer}_${region}",
      "class": "${layer}",
      "Datasource": {
        "file": "/home/mdione/src/projects/osm/data/osm/${region}/${layer}.shp"
      },
      "srs-name": "autodetect",
      "srs": "",
      "advanced": {},
      "name": "${layer}_${region}"
    }
EOS
) > ../../tilemill/project/osm-tilemill/input/${layer}_${region}.mml
done
