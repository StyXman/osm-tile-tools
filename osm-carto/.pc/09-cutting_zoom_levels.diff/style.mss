Map {
  background-color: @land-color;
}

@book-fonts:    "DejaVu Sans Book", "Arundina Regular", "Padauk Regular", "Khmer OS Metal Chrieng Regular",
                "TSCu_Paranar Regular", "Tibetan Machine Uni Regular",
                "Droid Sans Fallback Regular", "Unifont Medium";
@bold-fonts:    "DejaVu Sans Bold", "Arundina Bold", "Padauk Bold", "TSCu_Paranar Bold",
                "DejaVu Sans Book", "Arundina Regular", "Padauk Regular", "Khmer OS Metal Chrieng Regular",
                "TSCu_Paranar Regular", "Tibetan Machine Uni Regular",
                "Droid Sans Fallback Regular", "Unifont Medium";

@oblique-fonts: "DejaVu Sans Oblique", "Arundina Italic", "TSCu_Paranar Italic",
                "DejaVu Sans Book", "Arundina Regular", "Padauk Regular", "Khmer OS Metal Chrieng Regular",
                "TSCu_Paranar Regular", "Tibetan Machine Uni Regular",
                "Droid Sans Fallback Regular", "Unifont Medium";

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

@motorway-casing: darken(@motorway-fill, @darken-lighten);
@motorway-low-zoom: @motorway-fill;
@motorway-fill: #cf3030;
@motorway-tunnel-fill: lighten(@motorway-fill, @darken-lighten);

@trunk-casing: darken(@trunk-fill, @darken-lighten);
@trunk-low-zoom: #cf6868;
@trunk-fill: @motorway-fill;
@trunk-tunnel-fill: lighten(@trunk-fill, @darken-lighten);

@primary-casing: darken(@primary-fill, @darken-lighten);
@primary-low-zoom: @primary-fill;
@primary-fill: #8a5c00;
@primary-tunnel-fill: lighten(@primary-fill, @darken-lighten);

@secondary-casing: darken(@secondary-fill, @darken-lighten);
@secondary-low-zoom: @secondary-fill;
@secondary-fill: #2f6f2f;
@secondary-tunnel-fill: lighten(@secondary-fill, @darken-lighten);

@tertiary-casing: #444;
@tertiary-fill: #ffffff;
@tertiary-tunnel-fill: lighten(@tertiary-fill, 5%);

@residential-casing: #444;
@residential-fill: #ffffff;
@residential-tunnel-fill: lighten(@residential-fill, 10%);

@living-street-casing: @default-casing;
@living-street-fill: #ededed;

/*
minor roads for different zoom levels
tertiary    10-12
residential 12-13
road        10-
service     13
*/
@unimportant-road: #bbb;

@service-casing: #999;
@service-fill: @residential-fill;

@pedestrian-casing: grey;
@pedestrian-fill: #dddde8;

@road-casing: @residential-casing;
@road-fill: #ddd;

@path-casing: @default-casing;
@path-fill: black;

@footway-casing: @default-casing;
@footway-fill: salmon;

@steps-casing: @default-casing;
@steps-fill: @footway-fill;

@cycleway-casing: @default-casing;
@cycleway-fill: blue;

@bridleway-casing: @default-casing;
@bridleway-fill: green;

@byway-casing: @default-casing;
@byway-fill: #ffcc00;

@track-casing: @default-casing;
@track-fill: #996600;
@track-grade1-fill: #b37700;
@track-grade2-fill: #a87000;

@aeroway-fill: #bbc;
@runway-fill: @aeroway-fill;
@taxiway-fill: @aeroway-fill;
@helipad-fill: @aeroway-fill;

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
