.landuse {
  [type="railway"] {
    [zoom > 12] {
      polygon-fill: #dfdfdf;
    }
  }

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
}

.railways {
  [type="rail"] {
    [zoom>8] {
      /*
      ::outline {
      }
      */

      ::inline {
        line-color: #5f5f5f;
        line-width: 2;
        line-join: round;
        // line-dasharray: 5, 3;
      }
    }
  }
}

