  [type="tertiary_link"] {
    [zoom>13] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: @tertiary;
        line-width: 7;
        line-join: round;
      }
    }
    [zoom>14] {
      ::outline {
        line-color: @road-border;
        line-width: 11;
        line-join: round;
      }
      ::inner {
        line-color: @tertiary;
        line-width: 9;
        line-join: round;
      }
    }
  }

  [type="tertiary"] {
    [zoom>11] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: @tertiary;
        line-width: 7;
        line-join: round;
      }
    }
    [zoom > 13] {
        text-name: '[name]';
        text-face-name: @text;
        text-fill: @text-color;
        text-placement: line;
        text-halo-radius: 2;
        text-halo-fill: @text-halo;
        // text-min-path-length: 100;
        text-min-distance: 100;
    }
  }

  [type="secondary_link"] {
    [zoom>11] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: @secondary;
        line-width: 7;
        line-join: round;
      }
    }
  }

  [type="secondary"] {
    /*
    [zoom>6] {
      ::outline {
        line-color: @road-border;
        line-width: 4;
        line-join: round;
      }
      ::inner {
        line-color: @secondary;
        line-width: 3;
        line-join: round;
      }
    }
    */
    [zoom>8] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
      }
      ::inner {
        line-color: #7f7f00;
        line-width: 3;
        line-join: round;
      }
    }
    [zoom>10] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: @secondary;
        line-width: 7;
        line-join: round;
      }
    }
    [zoom>11] {
      ::text {
        text-name: '[ref]';
        text-face-name: @text;
        text-fill: #fff;
        text-placement: line;
        text-halo-radius: 3;
        text-halo-fill: @secondary;
        // text-min-path-length: 100;
        text-min-distance: 100;
      }
    }
    [zoom>13] {
      ::text {
        text-name: '[name]';
        text-face-name: @text;
        text-fill: @text-color;
        text-placement: line;
        text-halo-radius: 2;
        text-halo-fill: @text-halo;
        // text-min-path-length: 100;
        text-min-distance: 100;
      }
    }
  }

  [type="primary_link"] {
    [zoom>12] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: @primary;
        line-width: 7;
        line-join: round;
      }
    }
  }

  [type="primary"] {
    [zoom>6] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
      }
      ::inner {
        line-color: @primary;
        line-width: 3;
        line-join: round;
      }
    }
    [zoom>8] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: @primary;
        line-width: 7;
        line-join: round;
      }
    }
    [zoom>11] {
      ::text {
        text-name: '[ref]';
        text-face-name: @text;
        text-fill: #fff;
        text-placement: line;
        text-halo-radius: 4;
        text-halo-fill: @primary;
        text-min-path-length: 100;
        text-min-distance: 100;
      }
    }
    [zoom>13] {
      ::text {
        text-name: '[name]';
        text-face-name: @text;
        text-fill: @text-color;
        text-placement: line;
        text-halo-radius: 2;
        text-halo-fill: @text-halo;
        // text-min-path-length: 100;
        text-min-distance: 100;
      }
    }
  }

  [type="trunk_link"] {
    [zoom>11] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: #7f3f7f;
        line-width: 7;
        line-join: round;
      }
    }
  }

  [type="trunk"] {
    [zoom>7] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
      }
      ::inner {
        line-color: #7f3f7f;
        line-width: 3;
        line-join: round;
      }
    }
    [zoom>8] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: #7f3f7f;
        line-width: 7;
        line-join: round;
      }
    }
    [zoom > 13] {
        text-name: '[name]';
        text-face-name: @text;
        text-fill: @text-color;
        text-placement: line;
        text-halo-radius: 2;
        text-halo-fill: @text-halo;
        // text-min-path-length: 100;
        text-min-distance: 100;
    }
  }

  [type="motorway_link"] {
    [zoom>11] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: @motorway;
        line-width: 7;
        line-join: round;
      }
    }
  }

  [type="motorway"] {
    [zoom>4][zoom<=8] {
      /*
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
      }
      */
      ::inner {
        line-color: @motorway;
        line-width: 9;
        line-join: round;
      }
      ::line {
        line-color: #fff;
        line-width: 1;
        line-join: round;
      }
    }
    [zoom>8] {
      ::outline {
        line-color: @road-border;
        line-width: 11;
        line-join: round;
      }
      ::inner {
        line-color: @motorway;
        line-width: 9;
        line-join: round;
      }
      ::line {
        line-color: #fff;
        line-width: 1;
        line-join: round;
      }
      ::text {
        text-name: '[ref]';
        text-face-name: @text;
        text-fill: #fff;
        text-placement: line;
        text-halo-radius: 5;
        text-halo-fill: @motorway;
        // text-spacing: 100000;
        text-min-path-length: 100;
        text-min-distance: 100;
      }
    }
    [zoom>11] {
      ::outline {
        line-color: @road-border;
        line-width: 13;
        line-join: round;
      }
      ::inner {
        line-color: @motorway;
        line-width: 11;
        line-join: round;
      }
      ::line {
        line-color: #fff;
        line-width: 1;
        line-join: round;
      }
      ::text {
        text-name: '[ref]';
        text-face-name: @text;
        text-fill: #fff;
        text-placement: line;
        text-halo-radius: 5;
        text-halo-fill: @motorway;
        // text-spacing: 100000;
        text-min-path-length: 100;
        text-min-distance: 100;
      }
    }
  }
