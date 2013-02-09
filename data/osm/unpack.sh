#! /bin/bash

set -e

zip=$1
region=${zip%.shp.zip}

mkdir -pv ${region}

(
    cd ${region}
    unzip -u ../$zip
)

./generate_layers.sh $region

rm $zip
