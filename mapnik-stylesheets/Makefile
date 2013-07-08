all: 04-final.xml

04-final.xml: 03-amp_fixed.xml inc/colors.xml.inc remove_entities.awk
	xmllint --noent --load-trace --nonet $< | ./remove_entities.awk > $@

03-amp_fixed.xml: 02-strokes_colors_replaced.xml add_colors.awk
	sed -e 's/\&amp\;/\&/g;' $< | ./add_colors.awk > $@

02-strokes_colors_replaced.xml: 01-osm_linted.xml extract_strokes_widths.py
	./extract_strokes_widths.py $< $@ > /dev/null

inc/colors.xml.inc: 01-osm_linted.xml extract_strokes_widths.py
	./extract_strokes_widths.py $< /dev/null > $@

01-osm_linted.xml: osm.xml
	xmllint --noent --load-trace --nonet --output $@ $<

tile-clean:
	make -C tiles tile-clean

clean:
	rm 0*.xml
