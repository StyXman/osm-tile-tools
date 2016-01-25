function TripManager (map, trip) {
    var self= this;

    self.map= map;
    self.trip= trip;
    self.markers= [];

    self.mapClicked= function (e) {
        self.addPoint (e.latlng);
    }

    // self.addPoint= function (latlong, get_addr=true) {
    // default parameters is not recognized yet?
    self.addPoint= function (latlong, get_addr) {
        self.trip.addPoint (latlong);

        var marker= L.marker (latlong);
        self.markers.push ();
        marker.addTo (self.map);

        marker.on ('dblclick', self.markerDoubleClicked);

        if (get_addr) {
            var url= 'http://nominatim.openstreetmap.org/reverse';
            $.ajax (url, {
                'method': 'GET',
                'data': {
                    'format': 'json',
                    'lat': latlong.lat,
                    'lon': latlong.lng,
                    'zoom': 18
                },
                'crossDomain': true
            }).done (function (data, status, xhr) {
                self.setPopup (marker, data)
            });
        } else {
            // TODO
        }
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

    self.setPopup= function (marker, data) {
        marker.bindPopup (data.display_name);
        marker.openPopup ();
    }

    map.on ('singleclick', self.mapClicked);
}
