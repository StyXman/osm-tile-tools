@big-outer: #af3f3f;
@big-inner: #afaf3f;

.places {
  [population > 500000] {
    [zoom > 7][zoom < 12] {
      marker-width: 10;
      marker-fill: @big-inner;
      marker-line-color: @big-outer;
      marker-allow-overlap: true;
    }

    [zoom > 7][zoom < 15] {
        ::label {
          text-name: "[name]";
          text-face-name: @text;
          text-size: 16;
          text-fill: #000;
          text-halo-radius: 2;
          text-halo-fill: #fff;
          text-placement: point;
          text-allow-overlap: true;
        }
    }
  }

  [population < 500000][population > 100000] {
    [zoom > 7][zoom < 15] {
      marker-width: 7;
      marker-fill: @big-inner;
      marker-line-color: @big-outer;
      marker-allow-overlap: true;

      ::label {
          text-name: '[name]';
          text-face-name: @text;
          text-size: 14;
          text-fill: #000;
          text-halo-radius: 2;
          text-halo-fill: #fff;
          text-allow-overlap: true;
      }
    }
  }

  [population < 100000][population > 50000] {
    [zoom > 7][zoom < 15] {
      marker-width: 7;
      marker-fill: @big-inner;
      marker-line-color: @big-outer;
      marker-allow-overlap: true;

      ::label {
          text-name: '[name]';
          text-face-name: @text;
          text-size: 12;
          text-fill: #000;
          text-halo-radius: 2;
          text-halo-fill: #fff;
          text-allow-overlap: true;
      }
    }
  }
}

