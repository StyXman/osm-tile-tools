@water: #b8dee6;

.waterways {
  [type="river"] {
    [zoom > 7] {
      ::inner {
        line-color: @water;
        line-width: 1;
        line-join: round;
      }
    }
    [zoom >= 9] {
      ::inner {
        line-color: @water;
        line-width: 2;
        line-join: round;
      }
    }
    [zoom >= 11] {
      ::inner {
        line-color: @water;
        line-width: 4;
        line-join: round;
      }
    }
  }
  [type="stream"] {
    [zoom > 9] {
      ::inner {
        line-color: @water;
        line-width: 1;
        line-join: round;
      }
    }
    [zoom >= 11] {
      ::inner {
        line-color: @water;
        line-width: 2;
        line-join: round;
      }
    }
  }
}

