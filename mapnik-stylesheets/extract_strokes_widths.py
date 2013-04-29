#! /usr/bin/env python

from lxml import etree
import sys
from collections import defaultdict

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

color_map= {
    # motorway
    '#506077': '#000',
    '#809bc0': '#3f3f7f',
    '#d6dfea': '#6f6faf',

    # trunk
    '#477147': '#000',
    '#a9dba9': '#9f6f9f',
    '#cdeacd': '#cf9fcf',

    # primary
    '#8d4346': '#000',
    '#ec989a': '#3f9f3f',
    '#f4c3c4': '#6fcf6f',

    # secondary
    '#a37b48': '#000',
    '#fed7a5': '#cfaf3f',
    '#fecc8b': '#cfaf3f',
    '#fee0b8': '#df9f6f',

    # tertiary
    '#ffffb3': '#7f7f7f',
    '#ffc': '#afafaf',
    }

# map
root= tree.getroot ()

entities= {}
colors= defaultdict (list)

for level1 in root.iter ('Style'):
    try:
        style= level1.attrib['name']
    except AttibuteError, e:
        print 'malformed style?', e
    else:
        for level2 in level1.iter ('Rule'):
            #<Rule>
               #<Filter>[highway] = 'pedestrian' or [highway]='service' or [highway]='footway' or [highway]='path'</Filter>
               #&maxscale_zoom14;
               #<LineSymbolizer stroke="grey" stroke-width="1"/>
            #</Rule>
            for level3 in level2.iter ('Filter'):
                # actually there should be only one
                # 'tertiary_link' and not [tunnel]='yes'
                suffix= level3.text

            for level3 in level2.iter ('LineSymbolizer'):
                color= level3.attrib['stroke']
                # 'escape' things in text
                stroke_name= ''.join ( [ c  for c in suffix.replace ('!=', '_isnot_').
                                                            replace ('=', '_is_').
                                                            replace ("''", 'empty').
                                                            replace ('>', '_gt_').
                                                            replace ('<', '_lt_').
                                                            replace (' ', '_').
                                                            replace ('(', 'a_').
                                                            replace (')', '_z').
                                                            replace ('-', 'minus_')
                                            if c not in "'[]" ] ).replace ('__', '_')

                # <!ENTITY maxscale_zoom0 "<MaxScaleDenominator>250000000000</MaxScaleDenominator>">
                entity= "%s_%s" % (style, stroke_name)
                if not entity in ignore:
                    level3.set ('stroke', "&%s;" % entity)
                    old= entities.get (entity, None)
                    if old is None:
                        # first seen
                        if not entity in ignore_first:
                            entities[entity]= color
                            # this is tricky: update the color with the new definition
                            # or keep it as before
                            colors[color_map.get (color, color)].append (entity)
                        else:
                            print "<!-- ignoring first %s: %s -->" % (entity, color)
                            entities[entity]= 'seen'
                    else:
                        if not entity in ignore_others:
                            if color!=old:
                                entities[entity]= color
                                colors[color_map.get (color, color)].append (entity)
                            else:
                                # repeated
                                pass
                        else:
                            print "<!-- ignoring other %s: %s -->" % (entity, color)
                else:
                    print "<!-- ignoring %s: %s -->" % (entity, color)

print
                    
for color in sorted (colors.keys ()):
    print "<!-- %s -->" % color
    for entity in colors[color]:
        print '<!ENTITY %s "%s">' % (entity, color)
    print 

tree.write (sys.argv[2])
