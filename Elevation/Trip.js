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
}
