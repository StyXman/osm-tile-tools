#! /bin/bash

set -e

for region in $(grep -v \# country_list.txt); do
    # dir_name=$(basename $region)
    file_name="$(basename $region)-latest.osm.pbf"

    echo "Checking $file_name"
    if ! [ -f $file_name ]; then
        ./pull_osm_data.sh $region
        # ./unpack.sh ${dir_name}.shp.zip
        sleep 300
    fi

    ./pull_height.sh $file_name
done
