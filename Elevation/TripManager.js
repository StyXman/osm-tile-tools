function TripManager (map, trip) {
    var self= this;

    self.map= map;
    self.trip= trip;
    self.markers= [];

    self.addPoint= function (e) {
        var latlong= e.latlng;

        self.trip.addPoint (latlong);

        var marker= L.marker (latlong);
        self.markers.push ();
        marker.addTo (self.map);

        marker.on ('dblclick', self.removePoint);
    };

    self.removePoint= function (e) {
        var marker= e.target;
        var latlong= marker.getLatLng ();

        self.trip.removePoint (latlong);

        marker.remove ();
    }

    self.load= function () {
        // TODO: try URL

        // try cookies
        tripFromCookie ('default', self);
    }

    map.on ('singleclick', self.addPoint);
}
