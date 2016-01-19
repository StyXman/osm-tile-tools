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
    // date == -1 expires it
    createCookie(name, '', -1);
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
