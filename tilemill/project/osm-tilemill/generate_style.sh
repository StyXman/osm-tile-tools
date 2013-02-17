#! /bin/bash

set -e

source ../../../layers.sh

(
    cd input
    for i in *.mss; do
        echo $i >&2
        cat $i
    done
) > style.mss
