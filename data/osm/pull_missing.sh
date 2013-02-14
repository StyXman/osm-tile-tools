#! /bin/bash

set -e

for region in $(cat country_list.txt); do
    dir_name=$(basename $region)

    echo "Checking $dir_name"
    if ! [ -d $dir_name ]; then
        ./pull.sh $region
        ./unpack.sh ${dir_name}.shp.zip
        sleep 300
    fi

    ./pull_height.sh $dir_name
done
