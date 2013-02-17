  [type="footway"] {
    [zoom>15] {
      ::outline {
        line-color: @road-border;
        line-width: 1;
        line-join: round;
        line-dasharray: 5, 3;
      }
    }
  }

  [type="cycleway"] {
    [zoom>15] {
      ::outline {
        line-color: @road-border;
        line-width: 2;
        line-join: round;
        line-dasharray: 5, 3;
      }
    }
  }

  /*
  [type="bridleway"] {
    [zoom>15] {
      ::outline {
        line-color: @road-border;
        line-width: 2;
        line-join: round;
        line-dasharray: 5, 3;
      }
      ::inner {
        line-color: ;
        line-width: 1;
        line-join: round;
        line-dasharray: 3, 2;
      }
    }
  }
  */

  [type="path"] {
    [zoom>15] {
      ::inner {
        line-color: @road-border;
        line-width: 1;
        line-join: round;
        line-dasharray: 3, 2;
      }
    }
  }

