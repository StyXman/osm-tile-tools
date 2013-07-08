#! /bin/bash

if [ $# -eq 1 ]; then
    dst=$1
    cp -Rv tiles/{legend*,Elevation.dgml,preview.png,Makefile} $dst/
else
    dst=tiles
fi

src=$(pwd)/$dst
dst=$HOME/.local/share/marble/maps/earth/Elevation
rm -fv $dst
ln -sv $src $dst 
