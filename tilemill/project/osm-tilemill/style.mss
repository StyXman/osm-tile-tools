// kate: syntax javascript; indent-width 2;

Map {
  background-color: #b8dee6;
}

#relief-vhd,
#slope-vhd,
#hillshade-vhd {
    raster-scaling: lanczos;
}

#hillshade-vhd {
  [zoom < 15] {
    raster-opacity: 0.3;
  }
  [zoom > 14] {
    raster-opacity: 0;
  }
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

#boundaries {
  ::outline {
    line-color: #7f007f;
    line-join: round;
    line-dasharray: 3,3;
  }
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

#motorway {
  [zoom>4] {
    ::outline {
      line-color: #fff;
      line-width: 5;
      line-join: round;
    }
    ::outline {
      line-color: #00007f;
      line-width: 3;
      line-join: round;
    }
  }
  [zoom>7] {
    ::outline {
      line-color: #fff;
      line-width: 7;
      line-join: round;
    }
    ::inner {
      line-color: #3f3f7f;
      line-width: 5;
      line-join: round;
    }
  }
}

#motorway_link {
  [zoom>9] {
    ::outline {
      line-color: #fff;
      line-width: 5;
      line-join: round;
    }
    ::inner {
      line-color: #3f3f7f;
      line-width: 3;
      line-join: round;
    }
  }
}

#primary, #primary_link {
  [zoom>6] {
    ::outline {
      line-color: #fff;
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

#trunk, #trunk_link {
  [zoom>7] {
    ::outline {
      line-color: #fff;
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

#secondary, #secondary_link {
  [zoom>10] {
    ::outline {
      line-color: #fff;
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

#tertiary {
  [zoom>11] {
    ::outline {
      line-color: #fff;
      line-width: 5;
      line-join: round;
    }
    ::inner {
      line-color: #7f7f7f;
      line-width: 3;
      line-join: round;
    }
  }
}
