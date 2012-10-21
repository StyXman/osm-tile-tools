// kate: syntax javascript; indent-width 2;

#countries {
  ::outline {
    line-color: #85c5d3;
    line-width: 2;
    line-join: round;
  }
  polygon-fill: #fff;
}

#osm-highway {
  /*[zoom>=3]*/[zoom=4] {
    [highway='motorway'] ::outline {
      line-color: #fff;
      line-width: 2;
      line-join: round;
    }
    [highway='motorway'] ::outline {
      line-color: #00007f;
      line-width: 1;
      line-join: round;
    }
  }
  /*
  [zoom>=5][zoom=6] {
    [highway='motorway'] ::outline {
      line-color: #fff;
      line-width: 5;
      line-join: round;
    }
    [highway='motorway'] ::outline {
      line-color: #00007f;
      line-width: 3;
      line-join: round;
    }
  }
  [zoom>6] {
    [highway='primary'] ::outline {
      line-color: #fff;
      line-width: 5;
      line-join: round;
    }
    [highway='primary'] ::inner {
      line-color: #7f0000;
      line-width: 3;
      line-join: round;
    }
  }
  [zoom>7] {
    [highway='motorway'] ::outline {
      line-color: #fff;
      line-width: 7;
      line-join: round;
    }
    [highway='motorway'] ::inner {
      line-color: #3f3f7f;
      line-width: 5;
      line-join: round;
    }

    [highway='trunk'] ::outline {
      line-color: #fff;
      line-width: 5;
      line-join: round;
    }
    [highway='trunk'] ::inner {
      line-color: #7f3f7f;
      line-width: 3;
      line-join: round;
    }
  }
  [zoom>9] {
    [highway='motorway_link'] ::outline {
      line-color: #fff;
      line-width: 7;
      line-join: round;
    }
    [highway='motorway_link'] ::inner {
      line-color: #3f3f7f;
      line-width: 5;
      line-join: round;
    }
  }
  [zoom>10] {
    [highway='secondary'] ::outline {
      line-color: #fff;
      line-width: 5;
      line-join: round;
    }
    [highway='secondary'] ::inner {
      line-color: #7f7f00;
      line-width: 3;
      line-join: round;
    }
  }
  [zoom>11] {
    [highway='tertiary'] ::outline {
      line-color: #fff;
      line-width: 5;
      line-join: round;
    }
    [highway='tertiary'] ::inner {
      line-color: #7f7f7f;
      line-width: 3;
      line-join: round;
    }
  }
  */
}

#osm-boundaries {
  [admin_level=8]::outline {
    line-color: #7f007f;
    line-join: round;
    line-dasharray: 3,3;
  }
}

#relief-vhd,
#slope-vhd,
#hillshade-vhd {
    raster-scaling: lanczos;
}

#relief-vhd {
  [zoom < 15] {
    raster-opacity:0.5;
  }
  [zoom > 14] {
    raster-opacity:0.8;
  }
  [zoom > 16] {
    raster-opacity:1;
  }
}

#slope-vhd {
  raster-opacity:1;
}

#hillshade-vhd {
  raster-opacity :0.3;
}
#hillshade-vhd [zoom > 14] {
  raster-opacity :0;
}

#contours1000 [zoom > 5] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.7;
}
#contours500 [zoom > 8] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.7;
}
#contours250 [zoom > 10] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.7;
}
#contours100 [zoom > 12] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.5;
}
#contours50 [zoom > 14] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.7;
}
#contours10 [zoom > 16] {
    line-color: #333;
    line-join: round;
    line-opacity: 0.3;
}
