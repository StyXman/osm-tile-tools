.railways {
  [type="rail"] {
    [zoom>8] {
      /*
      ::outline {
      }
      */

        /*
        ::inline {
            line-color: #5f5f5f;
            line-width: 2;
            line-join: round;
            // line-dasharray: 5, 3;
          }
        }
        */

      ::line {
        line-width: 3;
        line-color: #777;
      }
      ::dash {
        line-color: #fff;
        line-width: 1.5;
        line-dasharray: 6, 6;
      }
    }
  }

  /*
  [type="rail"] {
    
  }
  */

  [type="funicular"] {
  }
}

