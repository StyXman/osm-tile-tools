from generate_tiles import time2hms


def test_time2hms():
    assert time2hms   (0) == (0, 0,  0)
    assert time2hms  (59) == (0, 0, 59)
    assert time2hms  (60) == (0, 1,  0)
    assert time2hms(3600) == (1, 0,  0)
