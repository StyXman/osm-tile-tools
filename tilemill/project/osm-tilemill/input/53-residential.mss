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
  }

