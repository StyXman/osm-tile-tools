var SaveControl= L.Control.extend ({
    options: {
        position: 'topright'
    },

    /*
    initialize: function (opts) {
        L.Util.setOptions (this, options);

    }
    */

    onAdd: function (map) {
        // create the control container with a particular class name
        var container= L.DomUtil.create ('div', 'leaflet-control-save');

        var cookies= L.DomUtil.create ('div', 'leaflet-control-save-cookies', container);
        cookies.innerHTML= 'In browser cookies';
        cookies.controller= this;
        L.DomEvent.addListener (cookies, 'click', this.cookies);

        var rest= L.DomUtil.create ('div', 'leaflet-control-save-rest', container);
        rest.innerHTML= 'In server';
        rest.controller= this;
        L.DomEvent.addListener (rest, 'click', this.rest);

        L.DomEvent.disableClickPropagation(container);

        return container;
    },

    cookies: function (e) {
        cookieFromTrip (this.controller.options.manager.trip);
    },

    rest: function (e) {
        saveToREST (this.controller.options.manager.trip);
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

            manager.addPoint (latlong);
        }
    }
}

function saveToREST (trip) {
    var j= trip.toJson ();

    var ans= $.ajax ('http://192.168.0.42:5000/trips/default', {
        'method': 'POST',
        // 'data': window.JSON.stringify ({ 'trip': j}), // jQuery does not provide a shortcut for this...
        // 'data': { trip: window.JSON.stringify (j) }, // jQuery does not provide a shortcut for this...
        'data': 'trip='+window.JSON.stringify (j), // jQuery does not provide a shortcut for this...
        'crossDomain': true,
        'processData': false // TODO: find out why flask is not URLdecoding this
    })
    // debug
    .done(function() {
        alert( "success" );
    })
    .fail(function(j, t, e) {
        alert( "error" + t + e);
    });
}
