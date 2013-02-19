#contour1000 {
  [zoom > 7] {
    line-width: 1;
    line-color: #1f1f1f;
    line-smooth: 0.8;
    line-opacity: 0.8;
  }
  [zoom > 11] {
    line-width: 1.5;
    line-color: #1f1f1f;
    line-smooth: 0.8;
    line-opacity: 0.8;
  }
  [zoom > 11] {
    ::labels {
      text-name: "[height]";
      text-face-name: @text;
      text-halo-radius: 1;
      // text-opacity: 0.7;
      text-placement: line;
    }
  }
}

#contour500 {
  [zoom > 11] {
    line-width: 1;
    line-color: #1f1f1f;
    line-smooth: 0.8;
    line-opacity: 0.6;
  }
  [zoom > 11] {
    line-width: 1;
    line-color: #1f1f1f;
    line-smooth: 0.8;
    line-opacity: 0.8;
  }
  [zoom > 13] {
    ::labels {
      text-name: "[height]";
      text-face-name: @text;
      text-halo-radius: 1;
      text-opacity: 0.7;
      text-placement: line;
    }
  }
}

#contour100 {
  [zoom > 13] {
    line-width: 1;
    line-color: #1f1f1f;
    line-smooth: 0.8;
    line-opacity: 0.4;

    [zoom > 14] {
      ::labels {
        text-name: "[height]";
        text-face-name: @text;
        text-halo-radius: 1;
        // text-opacity: 0.7;
        text-placement: line;
      }
    }
  }
}

#contour10 {
  [zoom > 15] {
    line-width: 1;
    line-color: #1f1f1f;
    line-smooth: 0.8;
    line-opacity: 0.2;
  }
}

