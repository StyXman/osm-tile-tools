#! /bin/bash

set -e

tmp=$(tempfile --directory . --suffix .lst)
(
    for i in "$@"; do
        ./tile_list.py $(grep $1 bboxes.txt | cut --delimiter '=' --fields 2)
    done
) | sort --unique | tee $tmp | ./push-zagato.py \
    "Elevation" "/media/mdione/Nokia N9/local/share/marble/maps/earth/Elevation"

rm $tmp
