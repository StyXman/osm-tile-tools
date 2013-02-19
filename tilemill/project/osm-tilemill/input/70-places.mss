@big-outer: #af3f3f;
@big-inner: #afaf3f;

.places {
  [population < 500] {
    [zoom > 14] {
      ::label {
          text-name: '[name]';
          text-face-name: @text;
          text-size: 8;
          text-fill: @text-color;
          text-halo-radius: 1.5;
          text-halo-fill: @text-halo;
          text-allow-overlap: false;
      }
    }
  }

  [population < 10000][population >= 500] {
    [zoom = 14] {
      ::label {
          text-name: '[name]';
          text-face-name: @text;
          text-size: 10;
          text-fill: @text-color;
          text-halo-radius: 1.5;
          text-halo-fill: @text-halo;
          text-allow-overlap: false;
      }
    }
  }

  [population < 50000][population >= 10000] {
    [zoom > 7][zoom < 15] {
      ::label {
          text-name: '[name]';
          text-face-name: @text;
          text-size: 12;
          text-fill: @text-color;
          text-halo-radius: 2;
          text-halo-fill: @text-halo;
          text-allow-overlap: false;
      }
    }
  }

  [population < 100000][population >= 50000] {
    [zoom > 7][zoom < 15] {
      ::label {
          text-name: '[name]';
          text-face-name: @text;
          text-size: 14;
          text-fill: @text-color;
          text-halo-radius: 2;
          text-halo-fill: @text-halo;
          text-allow-overlap: false;
      }
    }
  }

  [population < 500000][population >= 100000] {
    [zoom > 7][zoom < 15] {
      ::label {
          text-name: '[name]';
          text-face-name: @text;
          text-size: 16;
          text-fill: @text-color;
          text-halo-radius: 2;
          text-halo-fill: @text-halo;
          text-allow-overlap: false;
      }
    }
  }

  [population >= 500000] {
    [zoom > 10][zoom < 15] {
        ::label {
          text-name: "[name]";
          text-face-name: @text;
          text-size: 18;
          text-fill: @text-color;
          text-halo-radius: 2;
          text-halo-fill: @text-halo;
          text-placement: point;
          text-allow-overlap: false;
        }
    }
  }
}

