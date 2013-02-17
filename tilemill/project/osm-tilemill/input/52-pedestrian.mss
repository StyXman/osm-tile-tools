  [type="steps"] {
    [zoom>15] {
      ::outline {
        line-color: @road-border;
        line-width: 3;
        line-join: round;
        line-dasharray: 3,1;
      }
    }
  }

  [type="pedestrian"] {
    [zoom>15] {
      /*
      ::outline {
        line-color: @road-border;
        line-width: 2;
        line-join: round;
      }
      */
      ::inner {
        line-color: @road-border;
        line-width: 2;
        line-join: round;
        line-dasharray: 3, 2;
      }
    }
  }

