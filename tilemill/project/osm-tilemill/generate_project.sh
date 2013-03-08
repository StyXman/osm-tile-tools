#! /bin/bash

set -e

source ../../../layers.sh

(
cd input
echo '{'
cat project.mml
echo '  "Layer": ['

cat relief.mml
cat contour.mml

#            vvvvvvv-- leave this unquoted
for layer in $layers; do
    echo $layer >&2
    # file_amount=$(ls -1 ${layer}_*.mml | wc -l)
    # file_count=0
    
    for file in ${layer}_*.mml; do
        echo $file >&2
        cat $file
        # file_count=$((file_count+1))
        # if [ "$file_count" -ne "$file_amount" ]; then
        echo "    ,"
        # fi
    done
    
    echo >&2
    # layer_count=$((layer_count+1))
    # if [ "$layer_count" -ne "$layer_amount" ]; then
    #     echo "    ,"
    # fi
done

# cat boundaries.mml

echo '  ],'
cat epilogue.mml

echo '}'
) > project.mml
