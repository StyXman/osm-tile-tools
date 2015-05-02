psql --user postgres --command "create database osm;"
psql --user postgres --file /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
psql --user postgres --file /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql
