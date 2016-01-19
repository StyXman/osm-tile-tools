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

        L.DomEvent.disableClickPropagation(container);

        return container;
    },

    cookies: function (e) {
        cookieFromTrip (this.controller.options.trip);
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

function markersFromCookies (map) {
    var cookies= readCookies ("marker");

    for (var i= 0; i<cookies.length; i++) {
        var cookie= cookies[i];

        var data= cookie.split (',');
        // it's lat,lon,text,url
        var marker= L.marker([data[0], data[1]]).addTo (map);
        // reconstruct the url in case it got split
        // var url= .join (',')
        if (data[3].length>0) {
            marker.bindPopup ('<a href="'+data[3]+'">'+data[2]+'</a>').openPopup ();
        } else {
            marker.bindPopup (data[2]).openPopup ();
        }
    }
}

