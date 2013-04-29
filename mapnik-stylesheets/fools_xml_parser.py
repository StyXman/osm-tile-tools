#! /usr/bin/python

import sys
import re
from StringIO import StringIO

test_xml=StringIO ("""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE Map [
<!ENTITY % entities SYSTEM "inc/entities.xml.inc">
%entities;
]>
<Map background-color="#b5d0d0" srs="&srs900913;" minimum-version="2.0.0">
  &fontset-settings;
<Style name="turning_circle-casing">
    <Rule>
      &maxscale_zoom15;
      &minscale_zoom16;
      <Filter>[int_tc_type]='tertiary'</Filter>
      <PointSymbolizer file="&symbols;/turning_circle-tert-casing.18.png" allow-overlap="true" ignore-placement="true"/>
    </Rule>
</Style>
&layer-water_features;
<Layer name="tunnels" status="on" srs="&osm2pgsql_projection;">
    <StyleName>tunnels-casing</StyleName>
    <StyleName>tunnels-fill</StyleName>
    <Datasource>
      <Parameter name="table">
      (select way,highway from &prefix;_line where highway in ('motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','residential','unclassified') and tunnel in ('yes','true','1') order by z_order) as roads
      </Parameter>
      &datasource-settings;
    </Datasource>
</Layer>
</Map>
""")

def leading_spaces (line):
    i= 0
    for c in line:
        if c==' ':
            i+= 1
        else:
            break

    return i

class ParseError (ValueError):
    pass

class XML (object):
    def __init__ (self):
        self.xml_decl= None
        self.children= []
        self.root= None

    def parse_line (self, f, line):
        text= line.strip ()

        # we just parse things in one line
        if   text.startswith ('<?'):
            self.xml_decl= XMLDecl.parse (f, line)
        elif text.startswith ('<!'):
            self.children.append (ProcessingInstruction.parse (f, line))
        elif text.startswith ('%'):
            self.children.append (DTDReference.parse (f, line))
        elif text.startswith ('&'):
            self.children.append (XMLReference.parse (f, line))
        elif text.startswith ('</'):
            raise ParseError (line)
        elif text.startswith ('<'):
            self.children.append (Tag.parse (f, line))

    @classmethod
    def parse (cls, f, line=None):
        self= XML () # TODO: fix this inconsistency

        if line is None:
            for line in f:
                self.parse_line (f, line)
        else:
            self.parse_line (f, line)

        return self

    def pprint (self):
        ans=  self.xml_decl.pprint ()
        ans+= "".join ([ child.pprint() for child in self.children if child is not None ])
        
        return ans

class Element (object):
    def __init__ (self, indent):
        self.indent= indent

    @classmethod
    def parse (cls, f, line):
        raise NotImplementedError

    def pprint (self, text):
        # print text
        return " "*self.indent+text+"\n"

class AttributedElement (Element):
    attr_parser= re.compile (r'(.+)="(.+)"')

    def __init__ (self, indent, open, tag, attrs, close):
        super (AttributedElement, self).__init__ (indent)
        self.open= open
        self.tag= tag
        self.attrs= attrs
        self.close= close

    @classmethod
    def parse (cls, f, line):
        d= {}
        data= line.split ()
        name= data[1:]

        for bit in data[1:]:
            g= cls.attr_parser.match (bit)
            if g is not None:
                attr, value= g.group (1, 2)
                d[attr]= value
            else:
                raise ParseError (line)

        self= cls (leading_spaces (line), name, d)
        return self

    def pprint (self):
        return super (AttributedElement, self).pprint ("%s%s %s%s" % (self.open, self.tag, " ".join (['%s="%s"' % (k, v) for (k, v) in self.attrs.items () ]), self.close))

class XMLDecl (AttributedElement):
    def __init__ (self, name, indent, attrs):
        super (XMLDecl, self).__init__ (indent, '<?', 'xml', attrs, '?>')

class ProcessingInstruction (Element):

    @classmethod
    def parse (cls, f, line):
        data= line.split ()
        if   data[0][2:]=='DOCTYPE':
            self= DocType.parse (f, line)
        elif data[0][2:]=='ENTITY':
            self= Entity.parse (f, line)

        return self

class DocType (ProcessingInstruction):
    #<!DOCTYPE Map [
    #<!ENTITY % entities SYSTEM "inc/entities.xml.inc">
    #%entities;
    #]>
    def __init__ (self, indent, name, children):
        super (DocType, self).__init__ (indent)
        self.name= name
        self.children= children

    @classmethod
    def parse (cls, f, line):
        data= line.split ()

        name= data[1]
        children= []

        # BUG: ensure we have a list of stuff

        line= f.readline ()
        while line is not None and not line.endswith (']>\n'):
            subxml= XML.parse (f, line)
            children+= subxml.children

            line= f.readline ()

        self= cls (leading_spaces (data[0]), name, children)
        return self

    def pprint (self):
        ans=  " "*self.indent+"<!DOCTYPE %s [\n" % self.name
        ans+= "".join ([ child.pprint () for child in self.children if child is not None ])
        ans+= " "*self.indent+"]>\n"

        return ans

class Entity (ProcessingInstruction):
    # <!ENTITY % entities SYSTEM "inc/entities.xml.inc">
    def __init__ (self, indent, type, name, foo, bar):
        super (Entity, self).__init__ (indent)
        self.type= type
        self.name= name
        self.foo= foo
        self.bar= bar

    @classmethod
    def parse (cls, f, line):
        data= line.split ()

        # strip the trailing >
        self= cls (leading_spaces (line), data[1], data[2], data[3], data[4][:-1])
        return self

    def pprint (self):
        return super (Entity, self).pprint ("<!ENTITY %s %s %s %s>\n" % (self.type, self.name, self.foo, self.bar))

class Reference (Element):
    def __init__ (self, indent, symbol, name):
        super (Reference, self).__init__ (indent)
        self.name= name
        self.symbol= symbol

    @classmethod
    def parse (cls, f, line):
        text= line.strip ()

        self= cls (leading_spaces (line), text[0], text[1:-1]) # remove lewading % and trailing ;
        return self

    def pprint (self):
        return super (XMLReference, self).pprint ("%s%s;" % (self.symbol, self.name))

class DTDReference (Reference):
    pass

class XMLReference (Reference):
    pass

class Tag (AttributedElement):
    #<Rule>
      #&maxscale_zoom15;
      #&minscale_zoom16;
      #<Filter>[int_tc_type]='tertiary'</Filter>
      #<PointSymbolizer file="&symbols;/turning_circle-tert-casing.18.png" allow-overlap="true" ignore-placement="true"/>
    #</Rule>

    @classmethod
    def parse (cls, f, line):
        # a mix fo AttributedElement.parse() and DocType.parse()
        d= {}
        data= line.split ()
        name= data[0][1:]
        if name[-1]=='>':
            name= name[:-1]

        for bit in data[1:]:
            g= cls.attr_parser.match (bit)
            if g is not None:
                attr, value= g.group (1, 2)
                d[attr]= value
            else:
                raise ParseError (line)

        children= []

        l= f.readline ()
        while l is not None and not l.endswith (']>\n'):
            print l
            try:
                subxml= XML.parse (f, l)
            except ParseError, e:
                l= e.args[0].strip ()
                
                if l.startswith ('</'):
                    # closing tag, does it match?
                    if l[2:-1]!=name:
                        raise e
            else:
                children+= subxml.children

                l= f.readline ()

        self= cls (leading_spaces (line), name, d, children)
        return self

if __name__=='__main__':
    x= XML.parse (test_xml)
    print x.pprint ()
