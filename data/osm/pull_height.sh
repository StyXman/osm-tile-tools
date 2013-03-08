#! /bin/bash

set -e

extent_file=$1/extent.txt

# Extent: (9.499995, 46.301027) - (17.212637, 49.067789)

west=$(cat $extent_file | awk 'BEGIN { FS= "[\\(\\),\\. ]" } { print $3 }')
south=$(cat $extent_file | awk 'BEGIN { FS= "[\\(\\),\\. ]" } { print $6 }')
east=$(cat $extent_file | awk 'BEGIN { FS= "[\\(\\),\\. ]" } { print $11 }')
north=$(cat $extent_file | awk 'BEGIN { FS= "[\\(\\),\\. ]" } { print $14 }')

echo $west, $south, $east, $north

(
declare -a mins maxs patterns

# -17, 32, -6, 42
if [ ${east:0:1} == "-" -a ${west:0:1} == "-" ]; then
    # reorder them for seq
    # -17 -6 -> 6 17
    mins=([0]="${east:1}")
    maxs=([0]="${west:1}")
    patterns=([0]="N\${lat}W\${long}")
    seqs=1

# -2, 42, 1, 45
elif [ ${west:0:1} == "-" ]; then
    # -2 1 -> 1 2 0 1
    mins=([0]="1" [1]="0")
    maxs=([0]="$(( ${west:1} + 1 ))" [1]="${east}")
    patterns=([0]="N\${lat}W\${long}" [1]="N\${lat}E\${long}")
    seqs=2

else
    mins=([0]="${west}")
    maxs=([0]="${east}")
    patterns=([0]="N\${lat}E\${long}")
    seqs=1
fi

cd ../height

for s in $( seq 0 $((seqs-1)) ); do
    min=${mins[$s]}
    max=${maxs[$s]}
    pattern=${patterns[$s]}

    for i in $(seq $min $max); do
        long=$(printf "%03d" $i)

        for j in $(seq $south $north); do
            lat=$(printf "%02d" $j)

            if ! [ -f $(eval "echo ${pattern}.hgt") ]; then
                echo "Getting $(eval "echo ${pattern}.hgt")"
                zip_file=$(eval "echo ${pattern}.zip")
                # http://www.viewfinderpanoramas.org/dem1/N47E006.zip
                if ! wget --no-verbose "http://www.viewfinderpanoramas.org/dem1/$zip_file" || file $zip_file | grep -q 'HTML document'; then
                    rm -f $zip_file
                    # http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Eurasia/N00E072.hgt.zip
                    zip_file=$(eval "echo ${pattern}.hgt.zip")
                    wget --no-verbose "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Eurasia/$zip_file" || true
                    # http://droppr.org/srtm/v4.1/6_5x5_TIFs/srtm_39_04.zip
                    # convert -180/180 -90/90 -> 1/72 1/24
                    # TODO: this calls for python
                    # wget --no-verbose "http://droppr.org/srtm/v4.1/6_5x5_TIFs/$zip_file" || true
                fi

                if [ -f $zip_file ]; then
                    echo "Got $zip_file"
                    unzip -u $zip_file || true
                    rm $zip_file
                fi

                sleep 10
            fi
        done
    done
done
)
