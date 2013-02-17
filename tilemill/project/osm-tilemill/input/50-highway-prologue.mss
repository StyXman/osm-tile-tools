@road-border: #000;

.roads {
  /*
  line-color: @road-border;
  line-width: 1;
  line-join: round;
  */

  [type="track"] {
    [zoom>15] {
      ::outline {
        line-color: @road-border;
        line-width: 2;
        line-join: round;
        line-dasharray: 5, 3;
      }
      ::inner {
        line-color: #7f7f00;
        line-width: 1;
        line-join: round;
        line-dasharray: 5, 3;
      }
    }
  }

