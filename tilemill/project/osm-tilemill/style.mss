// kate: syntax javascript; indent-width 2;

Map {
  background-color: #b8dee6;
}

#boundaries {
  ::outline {
    line-color: #7f007f;
    line-join: round;
    line-dasharray: 3, 3;
  }
}

#relief-vhd,
#slope-vhd,
#hillshade-vhd {
    raster-scaling: lanczos;
}

#hillshade-vhd {
  [zoom < 16] {
    raster-opacity: 0.5;
  }
  [zoom > 15] {
    raster-opacity: 0;
  }
}

#relief-vhd {
  [zoom < 16] {
    raster-opacity: 0.5;
  }
  /*
  [zoom > 14] {
    raster-opacity: 0.8;
  }
  [zoom > 16] {
    raster-opacity: 1;
  }
  */
}

#slope-vhd {
  raster-opacity: 0.5;
}

#contours1000 {
  [zoom > 5] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.7;
  }
  [zoom > 10] {
    ::labels {
      text-name: "[height]";
      text-face-name: "DejaVu Sans Book";
      text-halo-radius: 1;
      text-opacity: 0.7;
      text-placement: line;
    }
  }
}
#contours500 {
  [zoom > 8] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.7;
  }
  [zoom > 12] {
    ::labels {
      text-name: "[height]";
      text-face-name: "DejaVu Sans Book";
      text-halo-radius: 1;
      text-placement: line;
    }
  }
}
#contours250 {
  [zoom > 10][zoom < 12] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.7;
  }
}
#contours100 {
  [zoom > 12] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.5;
  }
  [zoom > 14] {
    ::labels {
      text-name: "[height]";
      text-face-name: "DejaVu Sans Book";
      text-halo-radius: 1;
      text-opacity: 0.7;
      text-placement: line;
    }
  }
}
#contours50 {
  [zoom > 14] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.7;
  }
  [zoom > 16] {
    ::labels {
      text-name: "[height]";
      text-face-name: "DejaVu Sans Book";
      text-halo-radius: 1;
      text-opacity: 0.7;
      text-placement: line;
    }
  }
}
#contours10 [zoom > 16] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.3;
}

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

@road-border: #000;

.roads {
  /*
  line-color: @road-border;
  line-width: 1;
  line-join: round;
  */

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
}

#places {
  marker-width:6;
  marker-fill:#f45;
  marker-line-color:#813;
  marker-allow-overlap:true;
}

#contour {
  [zoom > 11] {
    line-width: 1;
    line-color: #dc143c;
    line-smooth: 0.8;
    [zoom > 14] {
      ::labels {
        text-name: "[height]";
        text-face-name: "DejaVu Sans Book";
        text-halo-radius: 1;
        text-opacity: 0.7;
        text-placement: line;
      }
    }
  }
}
