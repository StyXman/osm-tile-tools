  [type="tertiary_link"] {
    [zoom>13] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
      }
      ::inner {
        line-color: #bfbfbf;
        line-width: 3;
        line-join: round;
      }
    }
    [zoom>14] {
      ::outline {
        line-color: @road-border;
        line-width: 7;
        line-join: round;
      }
      ::inner {
        line-color: #bfbfbf;
        line-width: 5;
        line-join: round;
      }
    }
  }

  [type="tertiary"] {
    [zoom>11] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
      }
      ::inner {
        line-color: #bfbfbf;
        line-width: 3;
        line-join: round;
      }
    }
  }

  [type="secondary_link"] {
    [zoom>11] {
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
  }

  [type="secondary"] {
    /*
    [zoom>6] {
      ::outline {
        line-color: @road-border;
        line-width: 2;
        line-join: round;
      }
      ::inner {
        line-color: #7f7f00;
        line-width: 1;
        line-join: round;
      }
    }
    */
    [zoom>8] {
      ::outline {
        line-color: @road-border;
        line-width: 3;
        line-join: round;
      }
      ::inner {
        line-color: #7f7f00;
        line-width: 2;
        line-join: round;
      }
    }
    [zoom>10] {
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
  }

  [type="primary_link"] {
    [zoom>12] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
      }
      ::inner {
        line-color: #7f0000;
        line-width: 3;
        line-join: round;
      }
    }
  }

  [type="primary"] {
    [zoom>6] {
      ::outline {
        line-color: @road-border;
        line-width: 3;
        line-join: round;
      }
      ::inner {
        line-color: #7f0000;
        line-width: 2;
        line-join: round;
      }
    }
    [zoom>8] {
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
      }
      ::inner {
        line-color: #7f0000;
        line-width: 3;
        line-join: round;
      }
    }
  }

  [type="trunk_link"] {
    [zoom>11] {
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
  }

  [type="trunk"] {
    [zoom>7] {
      ::outline {
        line-color: @road-border;
        line-width: 3;
        line-join: round;
      }
      ::inner {
        line-color: #7f3f7f;
        line-width: 2;
        line-join: round;
      }
    }
    [zoom>8] {
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
  }

  [type="motorway_link"] {
    [zoom>11] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: #3f3f7f;
        line-width: 7;
        line-join: round;
      }
    }
  }

  [type="motorway"] {
    [zoom>4] {
      /*
      ::outline {
        line-color: @road-border;
        line-width: 5;
        line-join: round;
      }
      */
      ::inner {
        line-color: #00007f;
        line-width: 5;
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
        line-width: 7;
        line-join: round;
      }
      ::inner {
        line-color: #3f3f7f;
        line-width: 5;
        line-join: round;
      }
    }
    [zoom>11] {
      ::outline {
        line-color: @road-border;
        line-width: 9;
        line-join: round;
      }
      ::inner {
        line-color: #3f3f7f;
        line-width: 7;
        line-join: round;
      }
    }
  }
