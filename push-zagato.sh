#! /bin/bash

set -e

tmp=$(tempfile -d . -s .lst)
for i in "$@"; do
    ./tile_list.py $(grep $1 bboxes.txt | cut -d '=' -f 2) >> $tmp
done

rsync --verbose --archive --update --inplace --delete --delete-during \
    --ignore-missing-args --stats \
    --files-from $tmp ./ "/media/sdc/local/share/marble/maps/earth/Elevation/"

rm $tmp
