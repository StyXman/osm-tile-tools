function Trip (name) {
    var self= this;

    self.name= name;
    self.points= [];

    self.addPoint = function (latlong) {
        self.points.push (latlong);
    }

    self.removePoint= function (latlong) {
        var pos= self.points.indexOf (latlong);
        self.points.splice (pos, 1);
    }

    self.toJson= function () {
        var data= { 'name': self.name, 'points': [] };

        for (var i= 0; i<self.points.length; i++) {
            var point= self.points[i];
            data['points'].push ([point.lat, point.lng])
        }

        return data;
    }
}
