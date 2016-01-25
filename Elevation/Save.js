var SaveControl= L.Control.extend ({
    options: {
        position: 'topright'
    },

    onAdd: function (map) {
        // create the control container with a particular class name
        var container= L.DomUtil.create ('div', 'leaflet-control-save leaflet-bar');
        container.innerHTML= 'Save';

        var cookies= L.DomUtil.create ('div', 'leaflet-control-save-cookies leaflet-control-save-button', container);
        cookies.innerHTML= 'In browser cookies';
        cookies.controller= this;
        L.DomEvent.addListener (cookies, 'click', this.cookies);

        var rest= L.DomUtil.create ('div', 'leaflet-control-save-rest leaflet-control-save-button', container);
        rest.innerHTML= 'In server';
        rest.controller= this;
        L.DomEvent.addListener (rest, 'click', this.rest);

        var router= L.DomUtil.create ('div', 'leaflet-control-save-router leaflet-control-save-button', container);
        router.innerHTML= 'Calculate route';
        router.controller= this;
        L.DomEvent.addListener (router, 'click', this.route);

        L.DomEvent.disableClickPropagation(container);

        return container;
    },

    cookies: function (e) {
        cookieFromTrip (this.controller.options.manager.trip);
    },

    rest: function (e) {
        saveToREST (this.controller.options.manager.trip);
    },

    route: function (e) {
        calculateRoute (this.controller.options.manager.map, this.controller.options.manager.trip);
    }
});

function formatLatLng (point) {
    return point.lat+','+point.lng;
}

function cookieFromTrip (trip) {
    var data= '';

    // format is lat,lon[,text[,url]]:...
    var len= trip.points.length;

    for (var i= 0; i<len-1; i++) {
        var point= trip.points[i];
        data= data+formatLatLng (point)+':';
    }
    data= data+formatLatLng (trip.points[len-1]);

    createCookie ('tripplanner_trip_'+trip.name, data, 30);
}

function tripFromCookie (name, manager) {
    var cookie= readCookie ('tripplanner_trip_'+name);

    if (cookie) {
        var data= cookie.split (':');
        for (var i= 0; i<data.length; i++) {
            var coords= data[i].split (',');
            // the doc does not say so, but latLng() accepts an array
            var latlong= L.latLng (coords);

            manager.addPoint (latlong, false); // avoid a storm of calls
        }
    }
}

function saveToREST (trip) {
    var j= trip.toJson ();

    var ans= $.ajax ('http://grulicueva.homenet.org:5000/trips/default', {
        'method': 'POST',
        'data': { trip: window.JSON.stringify (j) }, // jQuery does not provide a shortcut for this...
        'crossDomain': true
    })
    // debug
    .done(function() {
        alert( "success" );
    })
    .fail(function(j, t, e) {
        alert( "error" + t + e);
    });
}

function calculateRoute (map, trip) {
    var locs= [];
    for (var i= 0; i<trip.points.length; i++) {
        locs.push (trip.points[i].lat+','+trip.points[i].lng);
    }

    $.ajax ('http://router.project-osrm.org/viaroute', {
        'method': 'GET',
        'data': {
            loc: locs,
            z: map.getZoom ()
        },
        'traditional': true,
        'crossDomain': true
    }).done (function (data, status) {
        var points= polyline.decode (data.route_geometry);
        var latlongs= points.map (function (e, i, a) {
            // 13:47 < RichardF> StyXman: divide by 10, OSRM has greater precision than the standard
            // yes, LatLng objects are created with the latLng() function...
            var latlong= L.latLng (e[0]/10, e[1]/10);
            return latlong;
        });
        var route= L.polyline (latlongs).addTo (map);
    });
}
