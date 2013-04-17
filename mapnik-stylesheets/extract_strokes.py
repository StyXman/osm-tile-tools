#! /usr/bin/env python

from lxml import etree
import sys

parser = etree.XMLParser(resolve_entities=False)

tree= etree.parse (sys.argv[1], parser=parser)

# ignore the first definition
ignore_first= (
    )
# ignore definitions starting from the second one
ignore_others= (
    'minor-roads-casing_a_highway__is__residential_or_highway__is__unclassified_or_highway__is__road_z_and_not_tunnel_is_yes',
    'minor-roads-fill_highway__is__steps',
    'guideways_railway__is__tram_and_bridge_is_yes',
    )
# completely ignore
ignore= (
    'minor-roads-fill_railway__is__rail_and_tunnel__is__yes',
    'minor-roads-fill_railway__is__rail_and_not_tunnel__is__yes',
    'minor-roads-fill_railway__is__spurminus_sidingminus_yard_and_tunnel__is__yes',
    'minor-roads-fill_railway__is__spurminus_sidingminus_yard_and_not_tunnel__is__yes',
    'minor-roads-fill_a_railway_is_narrow_gauge_or_railway_is_funicular_z_and_tunnel_is_yes',
    'minor-roads-fill_a_highway__is__cycleway_or_a_highway__is__path_and_bicycle__is__designated_z_z_and_not_tunnel__is__yes',
    'minor-roads-fill_highway__is__platform_or_railway__is__platform',
    )

# map
root= tree.getroot ()

entities= {}

for level1 in root.iter ('Style'):
    # style
    try:
        style= level1.attrib['name']
    except AttibuteError, e:
        print 'malformed style?', e
    else:
        for level2 in level1.iter ('Rule'):
            # rule
            for level3 in level2.iter ('Filter'):
                # actually there should be only one
                # 'tertiary_link' and not [tunnel]='yes'
                suffix= level3.text
                # print name, suffix
                
            for level3 in level2.iter ('LineSymbolizer'):
                # linesymbolizer stroke
                color= level3.attrib['stroke']
                # print color
                # 'escape' things in text
                name= ''.join ([ c for c in suffix.replace ('!=', '_isnot_').replace ('=', '_is_').replace ("''", 'empty').replace ('>', '_gt_').replace ('<', '_lt_').replace (' ', '_').replace ('(', 'a_').replace (')', '_z').replace ('-', 'minus_') if c not in "'[]"])

                # <!ENTITY maxscale_zoom0 "<MaxScaleDenominator>250000000000</MaxScaleDenominator>">
                entity= "%s_%s" % (style, name)
                if not entity in ignore:
                    old= entities.get (entity, None)
                    if old is None:
                        # first seen
                        if not entity in ignore_first:
                            entities[entity]= color
                            # print '<!ENTITY %s "%s">' % (entity, color)
                            level3.set ('stroke', "&%s;" % entity)
                        else:
                            print "<!-- ignoring first %s: %s -->" % (entity, color)
                            entities[entity]= 'seen'
                    else:
                        if not entity in ignore_others:
                            if color!=old:
                                entities[entity]= color
                                if old!='seen':
                                    # print "<!-- redefining entity [ %s ] -->" % old
                                    pass
                                # print '<!ENTITY %s "%s">' % (entity, color)
                                level3.set ('stroke', "&%s;" % entity)
                            else:
                                # repeated
                                pass
                        else:
                            print "<!-- ignoring other %s: %s -->" % (entity, color)
                else:
                    print "<!-- ignoring %s: %s -->" % (entity, color)

for entity in sorted (entities.keys ()):
    color= entities[entity]
    print '<!ENTITY %s "%s">' % (entity, color)

tree.write (sys.argv[2])
