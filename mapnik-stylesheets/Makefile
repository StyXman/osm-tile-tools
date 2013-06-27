all: 04-final.xml

04-final.xml: 03-amp_fixed.xml inc/colors.xml.inc
	xmllint --noent --load-trace --nonet $< | ./fix_baz.awk > $@

03-amp_fixed.xml: 02-strokes_colors_replaced.xml
	sed -e 's/\&amp\;/\&/g;' $< > $@

02-strokes_colors_replaced.xml: 01-osm_linted.xml
	./extract_strokes_widths.py $< $@ > /dev/null

inc/colors.xml.inc: 01-osm_linted.xml
	./extract_strokes_widths.py $< /dev/null > $@

01-osm_linted.xml: osm.xml
	xmllint --noent --load-trace --nonet --output $@ $<

tile-clean:
	make -C tiles tile-clean
