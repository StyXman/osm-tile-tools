.natural {
  [type="park"] {
    [zoom>12] {
      polygon-fill: #3f7f3f;
      /*
      line-color: #7f7f3f;
      line-width: 2;
      line-join: round;
      line-dasharray: 5, 3;
      */
    }
  }
  /*
  [type="forest"] {
    [zoom > 7] {
      polygon-fill: #007f00;
    }
  }
  */

  [type="riverbank"] {
    [zoom > 7] {
      polygon-fill: @water;
    }
  }
  [type="water"] {
    [zoom > 12] {
      polygon-fill: @water;
    }
  }
}

