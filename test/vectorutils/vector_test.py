#!/usr/bin/env python

# stdlib imports
import os.path
import sys

# third party
import numpy as np

import impactutils.vectorutils.vector as vector
from impactutils.vectorutils import point

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
sys.path.insert(0, shakedir)


def test():
    print('Testing Vector class...')
    a = vector.Vector(1, 1, 1)
    b = vector.Vector(2, 2, 2)
    c = vector.Vector(1, 1, 1)
    a_target = "<bound method Vector.__repr__ of <x=1.0000,y=1.0000,z=1.0000>>"
    b_target = "<bound method Vector.__repr__ of <x=2.0000,y=2.0000,z=2.0000>>"
    c_target = "<bound method Vector.__repr__ of <x=1.0000,y=1.0000,z=1.0000>>"
    assert str(a.__repr__) == a_target
    assert str(b.__repr__) == b_target
    assert str(c.__repr__) == c_target
    np.testing.assert_almost_equal(a.getArray(), np.array([1, 1, 1]))
    assert a == c
    alen = a.mag()
    np.testing.assert_almost_equal(alen, 1.73205, decimal=5)
    anorm = a.norm()
    bnorm = b.norm()
    assert anorm == bnorm
    acrossb = a.cross(b)
    assert acrossb == vector.Vector(0, 0, 0)
    adotb = a.dot(b)
    assert adotb == 6
    aplusb = a + b
    np.testing.assert_almost_equal(
        aplusb.getArray(),
        np.array([3, 3, 3]))

    pt = point.Point(-122.1, 36.2, 0)
    ptv = vector.Vector.fromPoint(pt)
    np.testing.assert_almost_equal(ptv.x, -2738256.0888039423)
    np.testing.assert_almost_equal(ptv.y, -4365154.23373464)
    np.testing.assert_almost_equal(ptv.z, 3746122.716409767)

    pt2 = ptv.toPoint()
    np.testing.assert_almost_equal(pt2.x, pt.x)
    np.testing.assert_almost_equal(pt2.y, pt.y)
    np.testing.assert_almost_equal(pt2.z, pt.z)

    ptvt = ptv.getTuple()
    np.testing.assert_almost_equal(
        ptvt,
        (-2738256.0888039423, -4365154.23373464, 3746122.716409767))
    dist = a.distance(b)
    np.testing.assert_almost_equal(dist, 1.7320508)
    assert a == c
    d = 2.4 * a
    np.testing.assert_almost_equal(d.x, 2.4000)
    np.testing.assert_almost_equal(d.y, 2.4000)
    np.testing.assert_almost_equal(d.z, 2.4000)
    d = a * 2.4
    np.testing.assert_almost_equal(d.x, 2.4000)
    np.testing.assert_almost_equal(d.y, 2.4000)
    np.testing.assert_almost_equal(d.z, 2.4000)
    e = a - b
    np.testing.assert_almost_equal(e.x, -1.)
    np.testing.assert_almost_equal(e.y, -1.)
    np.testing.assert_almost_equal(e.z, -1.)

    print('Passed Vector class tests.')


if __name__ == '__main__':
    test()
