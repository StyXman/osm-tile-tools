# kate: replace-tabs: off; indent-width 8

height_files = $(wildcard src/*.hgt)
master = mixed.tif
hillshade = mixed_hillshade.tif
slopeshade = mixed_slopeshade.tif
relief = mixed_relief.tif
# shapefiles = $(foreach heigh_file, $(height_files), $(basename $(height_file)) )

gopts = -co compress=lzw 

all: $(hillshade) $(relief) $(slopeshade) contour.shp 
# $(shapefiles)

# TODO: gdalinfo /vsizip/N43E016.zip/N43E006.hgt
$(master): $(height_files)
	gdal_merge.py -o $@ -v $^

$(hillshade): $(master)
	gdaldem hillshade $(gopts) $< $@

$(relief): $(master) color-relief.txt
	gdaldem color-relief $(gopts) $< color-relief.txt $@

$(slopeshade): mixed_slope.tif slope.txt
	gdaldem color-relief $(gopts) $< slope.txt $@

mixed_slope.tif: $(master)
	gdaldem slope $(gopts) -p $< $@

define gdal-contour
gdal_contour -i 10 -snodata 32767 -a height $< .
shapeindex $(basename )
endef

define shp2pgsql
shp2pgsql -c -I -g way $(basename $<) contours > $@
endef

mixed_contour.sql: contour.shp
	$(shp2pgsql)

contour.shp: $(master)
	$(gdal-contour)

# %.sql: %.shp
# 	$(shp2pgsql)

# %.shp: %.hgt
# 	$(gdal-contour)
