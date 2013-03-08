.landuse {
  /*
  [type="railway"] {
    [zoom > 12] {
      polygon-fill: #dfdfdf;
    }
  }
  */

  /* parks */
  [type="recreation_ground"] {
    [zoom>12] {
      polygon-fill: #3f7f3f;
    }
  }

  [type="reservoir"] {
    [zoom > 7] {
      polygon-fill: @water;
    }
  }

  [type="water"] {
    [zoom > 7] {
      polygon-fill: @water;
    }
  }

  [type="pond"] {
    [zoom > 7] {
      polygon-fill: @water;
    }
  }
}

