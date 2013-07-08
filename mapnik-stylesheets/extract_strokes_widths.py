#! /usr/bin/env python

from lxml import etree
import sys
from collections import defaultdict
import re

# read inc/entities.xml.inc to capture the scale denominators
mn_zooms= {None: 0}
mx_zooms= {}
mn= None
mx= None

f= open ('inc/entities.xml.inc')
#<!ENTITY maxscale_zoom1 "<MaxScaleDenominator>500000000</MaxScaleDenominator>">
#<!ENTITY minscale_zoom1 "<MinScaleDenominator>200000000</MinScaleDenominator>">
#<!ENTITY minscale_zoom18 "">
min_max_parser= re.compile ('<!ENTITY (min|max)scale_zoom(\d+) "(<(Min|Max)ScaleDenominator>(\d+)</.*>)?">')
for line in f:
    g= min_max_parser.search (line)
    if g is not None:
        what= g.group (1)
        zoom= g.group (2)
        scale= g.group (5)

        if what=='max':
            mx_zooms[scale]= zoom
        else:
            mn_zooms[scale]= zoom
f.close ()

parser = etree.XMLParser(resolve_entities=False)

tree= etree.parse (sys.argv[1], parser=parser)

style_names= (
    'highway-area-casing',
    'highway-area-fill',
    # 'highway-junctions', these are just text
    'tunnels-casing',
    'tunnels-fill',
    'minor-roads-casing-links',
    'minor-roads-casing',
    'minor-roads-fill-links',
    'minor-roads-fill',
    'footbikecycle-tunnels',
    'tracks-notunnel-nobridge',
    'tracks-tunnels',
    'waterway-bridges',
    'bridges_casing',
    'bridges_casing2',
    'bridges_fill',
    'roads',
    'trams',
    'guideways',
    )

# ignore the first definition
ignore_first= (
    )
# ignore definitions starting from the second one
ignore_others= (
    'minor-roads-casing_a_highway_is_residential_or_highway_is_unclassified_or_highway_is_road_z_and_not_tunnel_is_yes',
    'minor-roads-fill_highway_is_steps',
    'guideways_railway_is_tram_and_bridge_is_yes',
    )
# completely ignore
ignore= (
    'minor-roads-fill_railway_is_rail_and_tunnel_is_yes',
    'minor-roads-fill_railway_is_rail_and_not_tunnel_is_yes',
    'minor-roads-fill_railway_is_spurminus_sidingminus_yard_and_tunnel_is_yes',
    'minor-roads-fill_railway_is_spurminus_sidingminus_yard_and_not_tunnel_is_yes',
    'minor-roads-fill_a_railway_is_narrow_gauge_or_railway_is_funicular_z_and_tunnel_is_yes',
    'minor-roads-fill_a_highway_is_cycleway_or_a_highway_is_path_and_bicycle_is_designated_z_z_and_not_tunnel_is_yes',
    'minor-roads-fill_highway_is_platform_or_railway_is_platform',
    )

color_map= {
    # motorway
    '#506077': '#000',
    '#809bc0': '#3086bf',
    '#d6dfea': '#82b6d9',

    # trunk
    '#477147': '#000',
    '#a9dba9': '#bf30bf',
    '#97d397': '#bf30bf',
    '#cdeacd': '#d982d9',

    # primary
    '#8d4346': '#000',
    '#ec989a': '#bf3030',
    '#f4c3c4': '#d98282',

    # secondary
    '#a37b48': '#000',
    '#fecc8b': '#3f7f3f',
    '#fed7a5': '#3f7f3f',
    '#fee0b8': '#82d982',

    # tertiary
    # '#ffffb3': '#402c84',
    # '#ffc'   : '#866fd7',
    }

# map
root= tree.getroot ()

color_entities= {}
size_entities= {}
colors= defaultdict (list)

def sanitize (s):
    return ''.join ([ c for c  in s.replace ('!=', '_isnot_').
                                    replace ('=', '_is_').
                                    replace ("''", 'empty').
                                    replace ('>', '_gt_').
                                    replace ('<', '_lt_').
                                    replace (' ', '_').
                                    replace ('(', 'q_').
                                    replace (')', '_p').
                                    replace ('-', '_minus_')
                                if c not in "'[]" ]).replace ('__', '_')

for level1 in root.iter ('Style'):
    try:
        style= level1.attrib['name']
    except AttibuteError, e:
        print 'malformed style?', e
    else:
        if style in style_names:
            for level2 in level1.iter ('Rule'):
                #<Rule>
                  #<Filter>[highway] = 'motorway' or [highway]='motorway_link'</Filter>
                  #<MaxScaleDenominator>200000</MaxScaleDenominator>
                  #<MinScaleDenominator>100000</MinScaleDenominator>
                  #<LineSymbolizer stroke="#506077" stroke-width="3" stroke-dasharray="4,2"/>
                #</Rule>
                for level3 in level2.iter ('Filter'):
                    # actually there should be only one
                    # [highway] = 'motorway' or [highway]='motorway_link'
                    suffix= level3.text

                # find the scale denominators
                mnzm= 0
                mxzm= 18
                # NOTE: these might seem inverted
                # well, yes, they are :)
                for level3 in level2.iter ('MaxScaleDenominator'):
                    mnzm= mx_zooms[level3.text]
                for level3 in level2.iter ('MinScaleDenominator'):
                    mxzm= mn_zooms[level3.text]
                
                for level3 in level2.iter ('LineSymbolizer'):
                    color= level3.attrib['stroke']
                    # 'escape' things in text
                    stroke_name= sanitize (suffix)

                    color_entity= "%s_%s" % (style, stroke_name)
                    size_entity= "%s_%s-%s_%s" % (stroke_name, mnzm, mxzm, style)
                    
                    if not color_entity in ignore:
                        level3.set ('stroke', "&%s;" % color_entity)
                        old= color_entities.get (color_entity, None)
                        if old is None:
                            # first seen
                            if not color_entity in ignore_first:
                                color_entities[color_entity]= color
                                # this is tricky: update the color with the new definition
                                # or keep it as before
                                colors[color_map.get (color, color)].append (color_entity)

                            else:
                                print "<!-- ignoring first %s: %s -->" % (color_entity, color)
                                color_entities[color_entity]= 'seen'
                        else:
                            if not color_entity in ignore_others:
                                if color!=old:
                                    color_entities[color_entity]= color
                                    colors[color_map.get (color, color)].append (color_entity)
                                else:
                                    # repeated
                                    pass
                            else:
                                print "<!-- ignoring other %s: %s -->" % (color_entity, color)
                                
                        # handle sizes too
                        size_entities[size_entity]= level3.attrib['stroke-width']
                        level3.set ('stroke-width', "&%s;" % size_entity)
                    else:
                        print "<!-- ignoring %s: %s -->" % (color_entity, color)
        else:
            print "<!-- ignoring style %s -->" % (style)

print
                    
for color in sorted (colors.keys ()):
    print "<!-- %s -->" % color
    for color_entity in colors[color]:
        print '<!ENTITY %s "%s">' % (color_entity, color)
    print

for size_entity in sorted (size_entities.keys ()):
    print '<!ENTITY %s "%s">' % (size_entity, size_entities[size_entity])

tree.write (sys.argv[2])
