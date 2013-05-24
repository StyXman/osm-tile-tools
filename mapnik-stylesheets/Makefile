all: quux.xml

quux.xml: baz.xml inc/colors.xml.inc
	xmllint --noent --load-trace --nonet $< | ./fix_baz.awk > $@

baz.xml: bar.xml
	sed -e 's/\&amp\;/\&/g;' $< > $@

bar.xml: foo.xml
	./extract_strokes_widths.py foo.xml bar.xml > inc/colors.xml.inc

foo.xml: osm.xml
	xmllint --noent --load-trace --nonet --output $@ $<
