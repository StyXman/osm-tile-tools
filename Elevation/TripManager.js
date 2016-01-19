function TripManager (map, trip) {
    var self= this;

    self.map= map;
    self.trip= trip;
    self.markers= [];

    self.mapClicked= function (e) {
        self.addPoint (e.latlng);
    }

    self.addPoint= function (latlong) {
        self.trip.addPoint (latlong);

        var marker= L.marker (latlong);
        self.markers.push ();
        marker.addTo (self.map);

        marker.on ('dblclick', self.markerDoubleClicked);
    };

    self.markerDoubleClicked= function (e) {
        self.removePoint (e.target);
    }

    self.removePoint= function (marker) {
        var latlong= marker.getLatLng ();

        self.trip.removePoint (latlong);

        marker.remove ();
    }

    self.load= function () {
        // TODO: try URL

        // try cookies
        tripFromCookie ('default', self);
    }

    map.on ('singleclick', self.mapClicked);
}
