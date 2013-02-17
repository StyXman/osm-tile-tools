#relief-vhd,
#slope-vhd,
#hillshade-vhd {
    raster-scaling: lanczos;
}

#hillshade-vhd {
  [zoom < 16] {
    raster-opacity: 0.5;
  }
  /*
  [zoom > 15] {
    raster-opacity: 0;
  }
  */
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

