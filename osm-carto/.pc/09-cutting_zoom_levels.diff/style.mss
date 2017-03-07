Map {
  background-color: @water-color;
}

/*
About fonts:

Noto is a font family that wants to cover most of Unicode with a harmonic
design across various scripts. We use Noto for most text, with some support
for backward-compatibility and Unifont as fallback.

By order:

1. Noto Sans is available for most scripts and it is used as a first choice.
Where available the UI version of the fonts is used. In some cases the UI version
has fewer glyphs, so both are listed. Most of the list is in alphabetical order,
but there are some exceptions

  - Noto Sans UI is before all other fonts
  - The CJK fonts are manually ordered. The used CJK font covers all CJK
    languages, but defaults to the japanese glyph style if various glyph
    styles are available. (We have to default to one of JP, KR, SC, TC because
    this carto style has no knowledge about what language the “names” tag
    contains. As in Korea Han characters are not so widely used, it seems
    better to default to either Chinese or Japanese. As Chinese exists in the
    two variants SC/TC, it won’t be a uniform rendering anyway. So we default
    to Japanese. However, this choise stays somewhat arbitrary and subjective.
    See also https://github.com/gravitystorm/openstreetmap-carto/issues/2208)

2. Noto provides three variants of Arabic: Noto Kufi Arabic, Noto Naskh Arabic
and Noto Nastaliq Urdu. Naskh is the most commonly used style of Arabic.
Furthermore, Noto Naskh is the Arabic font of the Noto family with the greatest
coverage and the only one that has an UI variant. Therefor this style uses
Noto Naskh Arabic UI. The Arabic fonts are placed behind Sans fonts because
they might re-define some commonly used signs like parenthesis or quotation
marks, and the arabic design should not overwrite the standard design.

3. Noto provides two variants of Emoji: Noto Color Emoji and Noto Emoji. The
colour variant is a SVG flavoured OpenType font that contains coloured emojis.
This is not useful in cartography, so we use the “normal” monochromatic
Noto Emoji.

4. The list still includes DejaVu for compatibility on systems without Noto.

5. Unifont. This is a fallback of last resort with excellent coverage.
Unifont Medium covers the whole Unicode BMP without surrogates and without PUA.
Unifont Upper Medium covers some parts of the other Unicode planes. Unifont
Medium Sample would cover the BMP PUA with replacement characters, but cannot
be used because Mapnik does not support SBIT TTF.
*/

/*
A regular style.
*/
@book-fonts:    "Noto Sans UI Regular",
                "Noto Sans CJK JP Regular",
                "Noto Sans Armenian Regular",
                "Noto Sans Balinese Regular",
                "Noto Sans Bamum Regular",
                "Noto Sans Batak Regular",
                "Noto Sans Bengali UI Regular",
                "Noto Sans Buginese Regular",
                "Noto Sans Buhid Regular",
                "Noto Sans Canadian Aboriginal Regular",
                "Noto Sans Cham Regular",
                "Noto Sans Cherokee Regular",
                "Noto Sans Coptic Regular",
                "Noto Sans Devanagari UI Regular", "Noto Sans Devanagari Regular",
                "Noto Sans Ethiopic Regular",
                "Noto Sans Georgian Regular",
                "Noto Sans Gujarati UI Regular", "Noto Sans Gujarati Regular",
                "Noto Sans Gurmukhi UI Regular",
                "Noto Sans Hanunoo Regular",
                "Noto Sans Hebrew Regular",
                "Noto Sans Javanese Regular",
                "Noto Sans Kannada UI Regular",
                "Noto Sans Kayah Li Regular",
                "Noto Sans Khmer UI Regular",
                "Noto Sans Lao UI Regular",
                "Noto Sans Lepcha Regular",
                "Noto Sans Limbu Regular",
                "Noto Sans Lisu Regular",
                "Noto Sans Malayalam UI Regular",
                "Noto Sans Mandaic Regular",
                "Noto Sans Mongolian Regular",
                "Noto Sans Myanmar UI Regular",
                "Noto Sans New Tai Lue Regular",
                "Noto Sans NKo Regular",
                "Noto Sans Ol Chiki Regular",
                "Noto Sans Oriya UI Regular", "Noto Sans Oriya Regular",
                "Noto Sans Osmanya Regular",
                "Noto Sans Samaritan Regular",
                "Noto Sans Saurashtra Regular",
                "Noto Sans Shavian Regular",
                "Noto Sans Sinhala Regular",
                "Noto Sans Sundanese Regular",
                "Noto Sans Symbols Regular",
                "Noto Sans Syriac Eastern Regular",
                "Noto Sans Syriac Estrangela Regular",
                "Noto Sans Syriac Western Regular",
                "Noto Sans Tagalog Regular",
                "Noto Sans Tagbanwa Regular",
                "Noto Sans Tai Le Regular",
                "Noto Sans Tai Tham Regular",
                "Noto Sans Tai Viet Regular",
                "Noto Sans Tamil UI Regular",
                "Noto Sans Telugu UI Regular",
                "Noto Sans Thaana Regular",
                "Noto Sans Thai UI Regular",
                "Noto Sans Tibetan Regular",
                "Noto Sans Tifinagh Regular",
                "Noto Sans Vai Regular",
                "Noto Sans Yi Regular",

                "Noto Naskh Arabic UI Regular",

                "DejaVu Sans Book",

                "Unifont Medium", "Unifont Upper Medium";

/*
A bold style is available for almost all scripts. Bold text is heavier than
regular text and can be used for emphasis. Fallback is a regular style.
*/
@bold-fonts:    "Noto Sans UI Bold",
                "Noto Sans CJK JP Bold",
                "Noto Sans Armenian Bold",
                "Noto Sans Bengali UI Bold",
                "Noto Sans Cham Bold",
                "Noto Sans Devanagari UI Bold", "Noto Sans Devanagari Bold",
                "Noto Sans Ethiopic Bold",
                "Noto Sans Georgian Bold",
                "Noto Sans Gujarati UI Bold", "Noto Sans Gujarati Bold",
                "Noto Sans Gurmukhi UI Bold",
                "Noto Sans Hebrew Bold",
                "Noto Sans Kannada UI Bold",
                "Noto Sans Khmer UI Bold",
                "Noto Sans Lao UI Bold",
                "Noto Sans Malayalam UI Bold",
                "Noto Sans Myanmar UI Bold",
                "Noto Sans Oriya UI Bold", "Noto Sans Oriya Bold",
                "Noto Sans Sinhala Bold",
                "Noto Sans Tamil UI Bold",
                "Noto Sans Telugu UI Bold",
                "Noto Sans Thaana Bold",
                "Noto Sans Thai UI Bold",
                "Noto Sans Tibetan Bold",

                "Noto Sans CJK JP Regular",
                "Noto Sans Balinese Regular",
                "Noto Sans Bamum Regular",
                "Noto Sans Batak Regular",
                "Noto Sans Buginese Regular",
                "Noto Sans Buhid Regular",
                "Noto Sans Canadian Aboriginal Regular",
                "Noto Sans Cherokee Regular",
                "Noto Sans Coptic Regular",
                "Noto Sans Devanagari UI Regular", "Noto Sans Devanagari Regular",
                "Noto Sans Georgian Regular",
                "Noto Sans Gujarati UI Regular", "Noto Sans Gujarati Regular",
                "Noto Sans Hanunoo Regular",
                "Noto Sans Javanese Regular",
                "Noto Sans Kayah Li Regular",
                "Noto Sans Lepcha Regular",
                "Noto Sans Limbu Regular",
                "Noto Sans Lisu Regular",
                "Noto Sans Mandaic Regular",
                "Noto Sans Mongolian Regular",
                "Noto Sans New Tai Lue Regular",
                "Noto Sans NKo Regular",
                "Noto Sans Ol Chiki Regular",
                "Noto Sans Osmanya Regular",
                "Noto Sans Samaritan Regular",
                "Noto Sans Saurashtra Regular",
                "Noto Sans Shavian Regular",
                "Noto Sans Sundanese Regular",
                "Noto Sans Symbols Regular",
                "Noto Sans Syriac Eastern Regular",
                "Noto Sans Syriac Estrangela Regular",
                "Noto Sans Syriac Western Regular",
                "Noto Sans Tagalog Regular",
                "Noto Sans Tagbanwa Regular",
                "Noto Sans Tai Le Regular",
                "Noto Sans Tai Tham Regular",
                "Noto Sans Tai Viet Regular",
                "Noto Sans Tifinagh Regular",
                "Noto Sans Vai Regular",
                "Noto Sans Yi Regular",

                "Noto Naskh Arabic UI Bold",

                "Noto Naskh Arabic UI Regular",

                "DejaVu Sans Bold", "DejaVu Sans Book",

                "Unifont Medium", "Unifont Upper Medium";

/*
Italics are only available for the base font, not the other scripts.
For a considerable number of labels this style will make no difference to the regular style.
*/
@oblique-fonts: "Noto Sans UI Italic",
                "Noto Sans UI Regular",
                "Noto Sans CJK JP Regular",
                "Noto Sans Armenian Regular",
                "Noto Sans Balinese Regular",
                "Noto Sans Bamum Regular",
                "Noto Sans Batak Regular",
                "Noto Sans Bengali UI Regular",
                "Noto Sans Buginese Regular",
                "Noto Sans Buhid Regular",
                "Noto Sans Canadian Aboriginal Regular",
                "Noto Sans Cham Regular",
                "Noto Sans Cherokee Regular",
                "Noto Sans Coptic Regular",
                "Noto Sans Devanagari UI Regular", "Noto Sans Devanagari Regular",
                "Noto Sans Ethiopic Regular",
                "Noto Sans Georgian Regular",
                "Noto Sans Gujarati UI Regular", "Noto Sans Gujarati Regular",
                "Noto Sans Gurmukhi UI Regular",
                "Noto Sans Hanunoo Regular",
                "Noto Sans Hebrew Regular",
                "Noto Sans Javanese Regular",
                "Noto Sans Kannada UI Regular",
                "Noto Sans Kayah Li Regular",
                "Noto Sans Khmer UI Regular",
                "Noto Sans Lao UI Regular",
                "Noto Sans Lepcha Regular",
                "Noto Sans Limbu Regular",
                "Noto Sans Lisu Regular",
                "Noto Sans Malayalam UI Regular",
                "Noto Sans Mandaic Regular",
                "Noto Sans Mongolian Regular",
                "Noto Sans Myanmar UI Regular",
                "Noto Sans New Tai Lue Regular",
                "Noto Sans NKo Regular",
                "Noto Sans Ol Chiki Regular",
                "Noto Sans Oriya UI Regular", "Noto Sans Oriya Regular",
                "Noto Sans Osmanya Regular",
                "Noto Sans Samaritan Regular",
                "Noto Sans Saurashtra Regular",
                "Noto Sans Shavian Regular",
                "Noto Sans Sinhala Regular",
                "Noto Sans Sundanese Regular",
                "Noto Sans Symbols Regular",
                "Noto Sans Syriac Eastern Regular",
                "Noto Sans Syriac Estrangela Regular",
                "Noto Sans Syriac Western Regular",
                "Noto Sans Tagalog Regular",
                "Noto Sans Tagbanwa Regular",
                "Noto Sans Tai Le Regular",
                "Noto Sans Tai Tham Regular",
                "Noto Sans Tai Viet Regular",
                "Noto Sans Tamil UI Regular",
                "Noto Sans Telugu UI Regular",
                "Noto Sans Thaana Regular",
                "Noto Sans Thai UI Regular",
                "Noto Sans Tibetan Regular",
                "Noto Sans Tifinagh Regular",
                "Noto Sans Vai Regular",
                "Noto Sans Yi Regular",

                "Noto Naskh Arabic UI Regular",

                "DejaVu Sans Oblique", "DejaVu Sans Book",

                "Unifont Medium", "Unifont Upper Medium";

@water-color: #b5d0d0;
@water-dark: #5A5AA1;
@water-text: #5A5AA1;
@land-color: #f2efe9;

@standard-halo-radius: 1;
@standard-halo-fill: rgba(255,255,255,0.6);

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
