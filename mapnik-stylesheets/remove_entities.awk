#! /usr/bin/awk -f

BEGIN {
    entity_def=0;
    doctype_finished=0;
}

/entities.xml.inc/ {
    entity_def=1;
    print $0;
    print "%entities;";
}

/]>/ {
    doctype_finished=1;
}

{
    if (!entity_def || doctype_finished) {
        print $0;
    }
}
