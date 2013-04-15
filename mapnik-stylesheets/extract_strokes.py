#! /usr/bin/env python

from xml.etree import ElementTree
import sys

class AllEntities:
    def __getitem__(self, key):
        #key is your entity, you can do whatever you want with it here
        return key

parser = ElementTree.XMLParser()
parser.parser.UseForeignDTD(True)
parser.entity = AllEntities()

tree= ElementTree.parse (sys.argv[1], parser=parser)

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
      for level3 in level2:
        # filter
        if level3.tag=='Filter':
          # 'tertiary_link' and not [tunnel]='yes'
          suffix= level3.text
          # print name, suffix
        elif level3.tag=='LineSymbolizer':
          # linesymbolizer stroke
          color= level3.attrib['stroke']
          # print color
          # 'escape' things in text
          name= ''.join ([ c for c in suffix.replace ('!=', '_isnot_').replace ('=', '_is_').replace ("''", 'empty').replace ('>', '_gt_').replace ('<', '_lt_').replace (' ', '_').replace ('(', 'a_').replace (')', '_z').replace ('-', 'minus_') if c not in "'[]"])

          # <!ENTITY maxscale_zoom0 "<MaxScaleDenominator>250000000000</MaxScaleDenominator>">
          entity= "%s_%s" % (style, name)
          old= entities.get (entity, None)
          if old is None:
            entities[entity]= color
            print '<!ENTITY %s "%s">' % (entity, color)
          else:
            if color!=old:
              entities[entity]= color
              print "<!-- redefining entity -->"
              print '<!ENTITY %s "%s">' % (entity, color)

          level3.set ('stroke', "&%s;" % entity)

tree.write (sys.argv[2])
