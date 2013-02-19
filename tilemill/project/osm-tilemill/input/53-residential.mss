  [type="service"] {
    [zoom>15] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
      }
      ::inner {
        line-color: #5f5f5f;
        line-width: 3;
        line-join: round;
      }
    }
  }

  [type="road"] {
    [zoom>14] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
        line-cap: round;
      }
      ::inner {
        line-color: #7f7f7f;
        line-width: 3;
        line-join: round;
        line-cap: round;
      }
    }
    [zoom>15] {
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

  [type="living_street"] {
    [zoom>14] {
      ::outline {
        line-color: @road-border;
        line-width: 3;
        line-join: round;
        line-cap: round;
      }
      ::inner {
        line-color: #7f7f7f;
        line-width: 2;
        line-join: round;
        line-cap: round;
      }
    }
    [zoom>15] {
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

  [type="unclassified"] {
    [zoom>13] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
        line-cap: round;
      }
      ::inner {
        line-color: #7f7f7f;
        line-width: 3;
        line-join: round;
        line-cap: round;
      }
    }
    [zoom>15] {
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

  [type="residential"] {
    /*
    [zoom>12] {
      ::outline {
        line-color: @road-border;
        line-width: 3;
        line-join: round;
      }
      ::inner {
        line-color: #7f7f7f;
        line-width: 2;
        line-join: round;
      }
    }
    */
    [zoom>13] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
        line-cap: round;
      }
      ::inner {
        line-color: #7f7f7f;
        line-width: 3;
        line-join: round;
        line-cap: round;
      }
    }
    [zoom>15] {
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

