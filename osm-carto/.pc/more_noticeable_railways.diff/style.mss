Map {
  background-color: @land-color;
}

@book-fonts:    "DejaVu Sans Book", "Arundina Sans Regular", "Padauk Regular", "Khmer OS Metal Chrieng Regular",
                "TSCu_Paranar Regular", "Tibetan Machine Uni Regular",
                "Droid Sans Fallback Regular", "Unifont Medium";
@bold-fonts:    "DejaVu Sans Bold", "Arundina Sans Bold", "Padauk Bold", "TSCu_Paranar Bold",
                "DejaVu Sans Book", "Arundina Sans Regular", "Padauk Regular", "Khmer OS Metal Chrieng Regular",
                "TSCu_Paranar Regular", "Tibetan Machine Uni Regular",
                "Droid Sans Fallback Regular", "Unifont Medium";

@oblique-fonts: "DejaVu Sans Oblique", "Arundina Sans Italic", "TSCu_Paranar Italic",
                "DejaVu Sans Book", "Arundina Sans Regular", "Padauk Regular", "Khmer OS Metal Chrieng Regular",
                "TSCu_Paranar Regular", "Tibetan Machine Uni Regular",
                "Droid Sans Fallback Regular", "Unifont Medium";

// nice stuff is things that are not so common and that I like to see from far,
// like castles, viewpoints and such
@nice: 11;
// it's also the max general zoom level
@emergency: 14;
// things that are useful and common enough to see in the near range
@useful: 16;

@water-color: #b5d0d0;
@water-dark: #5A5AA1;
@water-text: #5A5AA1;
@land-color: #bfbfbf;

// admin
@admin-boundaries: purple;

// amenities
@attraction: #f2caea;
@barracks: #ff8f8f;

@darken-lighten: 15%;

// roads
@oneway: #aaa;

// @motorway-fill: #3030bf;
@motorway-fill: #cf3030;
@motorway-low-zoom: #e88b00;
@motorway-casing: darken(@motorway-fill, @darken-lighten);
@motorway-tunnel-fill: lighten(@motorway-fill, @darken-lighten);

// @trunk-fill: #bf30bf;
// @trunk-fill-alternative: #bf30bf;
@trunk-fill: @motorway-fill;
@trunk-low-zoom: @motorway-fill;
@trunk-casing: darken(@trunk-fill, @darken-lighten);
@trunk-tunnel-fill: lighten(@trunk-fill, @darken-lighten);

// @primary-fill: #bf3030;
@primary-fill: #8a5c00;
@primary-low-zoom: @primary-fill;
@primary-casing: darken(@primary-fill, @darken-lighten);
@primary-tunnel-fill: lighten(@primary-fill, @darken-lighten);

@secondary-fill: #2f6f2f;
@secondary-low-zoom: @secondary-fill;
@secondary-casing: darken(@secondary-fill, @darken-lighten);
@secondary-tunnel-fill: lighten(@secondary-fill, @darken-lighten);

// @tertiary-fill: #8a5c00;
@residential-fill: #ffffff;
@service-fill: #ffffff;
@living-street-fill: #ccc;
@pedestrian-fill: #ededed;
@road-fill: #ddd;
@path-fill: black;
@footway-fill: salmon;
@steps-fill: @footway-fill;
@cycleway-fill: blue;
@bridleway-fill: green;
@byway-fill: #ffcc00;
@track-fill: #996600;
@track-grade1-fill: #b37700;
@track-grade2-fill: #a87000;
@aeroway-fill: #bbc;
@runway-fill: @aeroway-fill;
@taxiway-fill: @aeroway-fill;
@helipad-fill: @aeroway-fill;

@tertiary-casing: #c6c68a;
@residential-casing: #bbb;
@service-casing: #999;
@living-street-casing: @default-casing;
@pedestrian-casing: grey;
@path-casing: @default-casing;
@footway-casing: @default-casing;
@steps-casing: @default-casing;
@cycleway-casing: @default-casing;
@bridleway-casing: @default-casing;
@byway-casing: @default-casing;
@track-casing: @default-casing;

@tertiary-tunnel-fill: lighten(@tertiary-fill, 5%);
@residential-tunnel-fill: lighten(@residential-fill, 10%);

// terrain-small [0-6], terrain-medium [7-8], terrain-big [9-]
.terrain {
  raster-scaling: lanczos;
  raster-opacity: 0.9;
  [zoom >= 7] { raster-opacity: 0.8; }
  [zoom >= 8] { raster-opacity: 0.7; }
}

// shade-small [0-6], shade-big [7]
.shade-over {
  comp-op: src-over;
  raster-scaling: lanczos;
  raster-opacity: 0.15;
}

// shade-medium [8], shade-big [9-]
.shade-overlay {
  raster-scaling: lanczos;
  [zoom >=8] {
    comp-op: overlay;
    raster-opacity: 0.5;
  }
}

// slope-small [0-6], slope-medium [7]
.slope-over {
  comp-op: src-over;
  raster-scaling: lanczos;
  raster-opacity: 0.4;
  [zoom >=  8] { raster-opacity: 0.27; }
  [zoom >=  9] { raster-opacity: 0.13; }
  [zoom >= 10] { raster-opacity: 0.0; }
}

// slope-medium [8], slope-big [9-]
.slope-overlay {
  raster-scaling: lanczos;
  comp-op: overlay;
  // comp-op: soft-light;
  raster-opacity: 0.7;
  [zoom >=  9] { raster-opacity: 0.8; }
  [zoom >= 10] { raster-opacity: 0.9; }
}

#contour-50 {
  [zoom >= 13] {
    line-color: #222;
    line-width: 0.5;
    line-smooth: 0.8;
    line-opacity: 0.2;
  }
}

#contour-100 {
  [zoom >= 11] {
    line-color: #222;
    line-width: 0.5;
    line-smooth: 0.8;
    line-opacity: 0.6;
  }

  [zoom >= 13] {
    text-name: "[height]";
    text-face-name: @book-fonts;
    text-size: 12;
    text-fill: #222;
    text-opacity: 0.6;
    text-halo-radius: 1;
    text-placement: line;
    text-spacing: 400;
  }
}

#contour-250 {
  [zoom = 10] {
    line-color: #222;
    line-width: 0.5;
    line-smooth: 0.8;
    line-opacity: 0.6;
  }
}

#contour-500 {
  [zoom >= 9] {
    line-color: #222;
    line-width: 0.5;
    line-smooth: 0.8;
    line-opacity: 0.6;
  }

  [zoom >= 11] {
    line-width: 0.75;
  }

  [zoom >= 12] {
    line-width: 1;

    text-name: "[height]";
    text-face-name: @book-fonts;
    text-size: 12;
    text-fill: #222;
    text-opacity: 0.6;
    text-halo-radius: 1;
    text-placement: line;
    text-spacing: 400;
  }
}

#contour-1000 {
  [zoom >= 8] {
    line-color: #222;
    line-width: 0.5;
    line-smooth: 0.8;
    line-opacity: 0.6;
  }

  [zoom >= 10] {
    line-width: 1.0;
  }

  [zoom >= 12] {
    // line-width: 1.5;

    text-name: "[height]";
    text-face-name: @book-fonts;
    text-size: 12;
    text-fill: #222;
    text-opacity: 0.6;
    text-halo-radius: 1;
    text-placement: line;
    text-spacing: 400;
  }
}

#pistes {
  [zoom >= 14] {
    [grade = 'novice'] {
      line-color: green;
    }
    [grade = 'easy'] {
      line-color: blue;
    }
    [grade = 'intermediate'] {
      line-color: red;
    }
    [grade = 'advanced'] {
      line-color: black;
    }

    line-width: 2;
    line-opacity: 0.6;
    line-smooth: 0.4;
  }

  [zoom >= 15] {
    line-width: 4;
    text-name: "[name]";
    text-size: 10;
    text-fill: #666;
    text-face-name: @book-fonts;
    text-halo-radius: 1;
    text-placement: line;
  }
}
