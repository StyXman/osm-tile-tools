Map {
  background-color: @land-color;
}

@book-fonts:    "DejaVu Sans Book", "Arundina Regular", "Arundina Sans Regular", "Padauk Regular", "Khmer OS Metal Chrieng Regular",
                "Mukti Narrow Regular", "Gargi Regular", "TSCu_Paranar Regular", "Tibetan Machine Uni Regular",
                "Droid Sans Fallback Regular", "Unifont Medium", "unifont Medium";
@bold-fonts:    "DejaVu Sans Bold", "Arundina Bold", "Arundina Sans Bold", "Padauk Bold", "TSCu_Paranar Bold",
                "DejaVu Sans Book", "Arundina Regular", "Arundina Sans Regular", "Padauk Regular", "Khmer OS Metal Chrieng Regular",
                "Mukti Narrow Regular", "gargi Medium", "TSCu_Paranar Regular", "Tibetan Machine Uni Regular",
                "Droid Sans Fallback Regular", "Unifont Medium", "unifont Medium";

@oblique-fonts: "DejaVu Sans Oblique", "Arundina Italic", "Arundina Sans Italic", "TSCu_Paranar Italic",
                "DejaVu Sans Book", "Arundina Regular", "Arundina Sans Regular", "Padauk Regular", "Khmer OS Metal Chrieng Regular",
                "Mukti Narrow Regular", "Gargi Regular", "TSCu_Paranar Regular", "Tibetan Machine Uni Regular",
                "Droid Sans Fallback Regular", "Unifont Medium", "unifont Medium";

@water-color: #b5d0d0;
@land-color: #bfbfbf;

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
