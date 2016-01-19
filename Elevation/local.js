// the following 3 functions are from
// http://www.quirksmode.org/js/cookies.html
function createCookie(name, value, days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        var expires = '; expires=' + date.toGMTString();
    }
    else var expires = '';
    document.cookie = name + '=' + value + expires + '; path=/';
}

function readCookie(name) {
    var nameEQ = name + '=';
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

function eraseCookie(name) {
    createCookie(name, '', - 1);
}

function readCookies(prefix) {
    var nameEQ = prefix + '_';
    var ca = document.cookie.split(';');
    var ans = [];
    j= 0;
    for (var i = 0; i < ca.length; i++) {
        var index = 0;
        var c = ca[i];
        while (c.charAt(index) == ' ') {
            index = index + 1;
        }
        if (c.indexOf(nameEQ) == index) {
            // keep reading, find the =
            while (c.charAt(index) != '=') {
                index = index + 1;
            }
            ans[j] = c.substring(index + 1, c.length);
            j= j+1;
        }
    }
    return ans;
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

function setup_map () {
    var map = L.map('map').setView([47.946,10.195], 5);

    L.tileLayer('http://grulicueva.homenet.org/~mdione/Elevation/{z}/{x}/{y}.png', {
        attribution: 'Map data (C) <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
        maxZoom: 18
    }).addTo(map);

    var hash = new L.Hash(map);

    // markersFromCookies (map);

    var geocoder = L.Control.geocoder({
        collapsed: false,
        showResultIcons: true
    });
    geocoder.addTo(map);
    geocoder.markGeocode = function(result) {
        this._map.fitBounds(result.bbox);
        return this;
    };
}
