#!/usr/bin/env python

# stdlib imports
import os.path
import sys

# third party imports
from openquake.hazardlib.geo.utils import OrthographicProjection
from openquake.hazardlib.gsim.abrahamson_2015 import AbrahamsonEtAl2015SInterHigh
import numpy as np
import time
import pytest

# local imports
from impactutils.rupture.distance import get_distance, Distance
from impactutils.rupture.gc2 import _computeGC2
from impactutils.rupture.origin import Origin
from impactutils.rupture.quad_rupture import QuadRupture
from impactutils.time.ancient_time import HistoricTime


do_tests = True


def test_san_fernando():
    # This is a challenging rupture due to overlapping and discordant
    # segments, as brought up by Graeme Weatherill. Our initial
    # implementation put the origin on the wrong side of the rupture.
    x0 = np.array([7.1845, 7.8693])
    y0 = np.array([-10.3793, -16.2096])
    z0 = np.array([3.0000, 0.0000])
    x1 = np.array([-7.8506, -7.5856])
    y1 = np.array([-4.9073, -12.0682])
    z1 = np.array([3.0000, 0.0000])
    x2 = np.array([-4.6129, -5.5149])
    y2 = np.array([3.9887, -4.3408])
    z2 = np.array([16.0300, 8.0000])
    x3 = np.array([10.4222, 9.9400])
    y3 = np.array([-1.4833, -8.4823])
    z3 = np.array([16.0300, 8.0000])

    epilat = 34.44000
    epilon = -118.41000
    proj = OrthographicProjection(
        epilon - 1, epilon + 1, epilat + 1, epilat - 1)
    lon0, lat0 = proj(x0, y0, reverse=True)
    lon1, lat1 = proj(x1, y1, reverse=True)
    lon2, lat2 = proj(x2, y2, reverse=True)
    lon3, lat3 = proj(x3, y3, reverse=True)

    # Rupture requires an origin even when not used:
    origin = Origin({'id': 'test', 'lat': 0, 'lon': 0,
                     'depth': 5.0, 'mag': 7.0, 'netid': '',
                     'network': '', 'locstring': '',
                     'time': HistoricTime.utcfromtimestamp(int(time.time()))})

    rup = QuadRupture.fromVertices(
        lon0, lat0, z0, lon1, lat1, z1, lon2, lat2, z2, lon3, lat3, z3,
        origin)
    # Make a origin object; most of the 'event' values don't matter
    event = {'lat': 0, 'lon': 0, 'depth': 0, 'mag': 6.61,
             'id': '', 'locstring': '', 'type': 'ALL',
             'netid': '', 'network': '',
             'time': HistoricTime.utcfromtimestamp(int(time.time()))}
    origin = Origin(event)

    # Grid of sites
    buf = 0.25
    lat = np.linspace(np.nanmin(rup._lat) - buf, np.nanmax(rup._lat) + buf, 10)
    lon = np.linspace(np.nanmin(rup._lon) - buf, np.nanmax(rup._lon) + buf, 10)
    lons, lats = np.meshgrid(lon, lat)
    dep = np.zeros_like(lons)
    x, y = proj(lon, lat)
    rupx, rupy = proj(rup._lon[~np.isnan(rup._lon)],
                      rup._lat[~np.isnan(rup._lat)])

    # Calculate U and T
    dtypes = ['repi', 'rhypo', 'rjb', 'rrup',
              'rx', 'ry', 'ry0', 'U', 'T', 'rvolc']
    dists = get_distance(dtypes, lats, lons, dep, rup)

    targetU = np.array(
        [[29.37395812, 22.56039569, 15.74545461, 8.92543078,
          2.09723735, -4.73938823, -11.58093887, -18.42177264,
          -25.25743913, -32.08635501],
         [31.84149137, 25.03129417, 18.22007124, 11.40292429,
          4.57583886, -2.26009972, -9.09790123, -15.92911065,
            -22.75071243, -29.56450963],
            [34.30623138, 27.49382948, 20.67774678, 13.85111535,
             7.0115472, 0.16942111, -6.65327488, -13.45181115,
             -20.24352643, -27.03530618],
            [36.78170249, 29.96380633, 23.1270492, 16.23906653,
             9.32934682, 2.41729624, -4.2732657, -10.94940844,
             -17.703852, -24.4792072],
            [39.29233805, 32.49155866, 25.68380903, 18.73823089,
             12.08780156, 5.99219619, -1.38387344, -8.28331275,
             -15.08759643, -21.87909368],
            [41.84662959, 35.09745097, 28.42432401, 21.98993679,
             15.2994003, 8.38037254, 1.3900846, -5.5601922,
             -12.4250749, -19.24690137],
            [44.41552101, 37.69652131, 31.0257236, 24.38573309,
             17.67059825, 10.84688716, 3.96604399, -2.920931,
             -9.78152208, -16.6132751],
            [46.97201328, 40.2558351, 33.55821495, 26.85923974,
             20.12416451, 13.33640001, 6.50905851, -0.33349597,
             -7.17138975, -13.99568321],
            [49.51154107, 42.79053584, 36.07536907, 29.35382731,
             22.61099757, 15.83894006, 9.04135415, 2.22928601,
             -4.58574545, -11.3959888],
            [52.03832734, 45.31289877, 38.58842009, 31.85764151,
             25.11309728, 18.35066231, 11.57145669, 4.78070229,
             -2.01505508, -8.81029694]])
    np.testing.assert_allclose(dists['U'], targetU, atol=0.01)

    targetT = np.array(
        [[-40.32654805, -38.14066537, -35.95781299, -33.79265063,
          -31.65892948, -29.56075203, -27.48748112, -25.41823592,
          -23.33452174, -21.22822801],
         [-32.28894353, -30.06603457, -27.83163648, -25.61482279,
            -23.45367121, -21.36959238, -19.34738882, -17.33510593,
            -15.28949735, -13.20224592],
            [-24.30254163, -22.03532096, -19.70590091, -17.35907062,
             -15.10840929, -13.02682541, -11.13554925, -9.25705749,
             -7.26675455, -5.19396824],
            [-16.41306482, -14.1418547, -11.68888578, -8.9318195,
             -6.39939727, -4.10984325, -2.85061088, -1.29211846,
             0.68929792, 2.78115216],
            [-8.63784529, -6.5089946, -4.32108309, -1.44275161,
             -0.05102145, -0.20890633, 3.92700516, 6.36977183,
             8.55572399, 10.72128633],
            [-0.88135778, 1.06766314, 2.77955566, 3.8241835,
             5.99212478, 8.76823285, 11.54715599, 14.0961506,
             16.4200502, 18.65346494],
            [6.98140207, 8.91888936, 10.77724993, 12.6499521,
             14.79454638, 17.18482779, 19.63520498, 22.03525644,
             24.35152986, 26.60592498],
            [14.95635952, 16.95134069, 18.94768299, 20.99811237,
             23.15975573, 25.42700742, 27.74302905, 30.0547134,
             32.33583361, 34.58421221],
            [22.9921068, 25.0353212, 27.09829391, 29.20364631,
             31.3678744, 33.58684524, 35.8383652, 38.09736043,
             40.34713771, 42.58152772],
            [31.05186177, 33.1252095, 35.21960344, 37.34488267,
             39.50633206, 41.70076344, 43.91762786, 46.14415669,
             48.37021739, 50.59029205]])
    np.testing.assert_allclose(dists['T'], targetT, atol=0.01)

    # new method:
    ddict = _computeGC2(rup, lons, lats, dep)
    np.testing.assert_allclose(ddict['T'], targetT, atol=0.01)
    np.testing.assert_allclose(ddict['U'], targetU, atol=0.01)
    d = Distance(AbrahamsonEtAl2015SInterHigh(), lats, lons, dep, rup)


def test_exceptions():
    # This is a challenging rupture due to overlapping and discordant
    # segments, as brought up by Graeme Weatherill. Our initial
    # implementation put the origin on the wrong side of the rupture.
    x0 = np.array([7.1845, 7.8693])
    y0 = np.array([-10.3793, -16.2096])
    z0 = np.array([3.0000, 0.0000])
    x1 = np.array([-7.8506, -7.5856])
    y1 = np.array([-4.9073, -12.0682])
    z1 = np.array([3.0000, 0.0000])
    x2 = np.array([-4.6129, -5.5149])
    y2 = np.array([3.9887, -4.3408])
    z2 = np.array([16.0300, 8.0000])
    x3 = np.array([10.4222, 9.9400])
    y3 = np.array([-1.4833, -8.4823])
    z3 = np.array([16.0300, 8.0000])

    epilat = 34.44000
    epilon = -118.41000
    proj = OrthographicProjection(
        epilon - 1, epilon + 1, epilat + 1, epilat - 1)
    lon0, lat0 = proj(x0, y0, reverse=True)
    lon1, lat1 = proj(x1, y1, reverse=True)
    lon2, lat2 = proj(x2, y2, reverse=True)
    lon3, lat3 = proj(x3, y3, reverse=True)

    # Rupture requires an origin even when not used:
    origin = Origin({'id': 'test', 'lat': 0, 'lon': 0,
                     'depth': 5.0, 'mag': 7.0, 'netid': '',
                     'network': '', 'locstring': '',
                     'time': HistoricTime.utcfromtimestamp(int(time.time()))})

    rup = QuadRupture.fromVertices(
        lon0, lat0, z0, lon1, lat1, z1, lon2, lat2, z2, lon3, lat3, z3,
        origin)

    target = "valid or is not implemented"
    with pytest.raises(NotImplementedError, match=target) as a:
        get_distance('invalid', 32, 105, 'dep', rup, dx=0.5)

    target = "must have the same shape"
    with pytest.raises(Exception, match=target) as a:
        get_distance('rx', np.asarray([32]), np.asarray(
            [105, 102]), 'dep', rup, dx=0.5)


if __name__ == "__main__":
    test_san_fernando()
    test_exceptions()
