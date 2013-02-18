all:
	# $(MAKE) -C data/osm
	$(MAKE) -C data/height
	$(MAKE) -C tilemill/project/osm-tilemill
