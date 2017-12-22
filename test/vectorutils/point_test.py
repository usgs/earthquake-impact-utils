#!/usr/bin/env python

from impactutils.vectorutils.point import Point
import numpy as np

def test_point():
    p1 = Point(1,2,3)
    assert p1.x == 1
    assert p1.y == 2
    assert p1.z == 3
    
    assert p1.longitude == 1
    assert p1.latitude == 2
    assert p1.depth == 3

    p2 = Point(4,5,6)
    az = p1.azimuth(p2)
    np.testing.assert_almost_equal(az,44.864709576125847)
    
if __name__ == '__main__':
    test_point()
