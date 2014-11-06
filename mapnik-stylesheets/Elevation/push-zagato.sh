#! /bin/bash

bbox_z=$(grep $1 bboxes.txt | cut -d '=' -f 2)
./tile_list.py $bbox_z > $1.lst

rsync --verbose --archive --update --inplace --files-from $1.lst ./ "/media/mdione/Nokia N9/local/share/marble/maps/earth/Elevation/"
