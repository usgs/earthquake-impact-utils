#!/usr/bin/env python

# stdlib imports
import os.path
import sys

# third party imports
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# local imports
from impactutils.mapping.city import Cities
from impactutils.mapping.mercatormap import MercatorMap

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))
mapiodir = os.path.abspath(os.path.join(homedir, '..'))
sys.path.insert(0, mapiodir)


def test_mmap(bounds=None):
    if bounds is None:
        bounds = xmin, ymin, xmax, ymax = \
            -121.046000, -116.046000, 32.143500, 36.278500
    else:
        xmin, ymin, xmax, ymax = bounds
    figsize = (7, 7)
    cities = Cities.fromDefault()
    mmap = MercatorMap(bounds, figsize, cities, padding=0.5)
    fig = mmap.figure
    ax = mmap.axes
    ax.coastlines(resolution="10m", zorder=10)
    mmap.drawCities(shadow=True)
    fig.canvas.draw()
    map = np.frombuffer(
        fig.canvas.tostring_rgb(), dtype=np.uint8)
    map_file = os.path.join(
        homedir, '../data/mercator_target.npz')
    map_target = np.load(map_file)
    np.testing.assert_array_equal(map, map_target['a'])


if __name__ == '__main__':
    if len(sys.argv) > 1:
        xmin = float(sys.argv[1])
        xmax = float(sys.argv[2])
        ymin = float(sys.argv[3])
        ymax = float(sys.argv[4])
        bounds = (xmin, xmax, ymin, ymax)
    else:
        bounds = None
    test_mmap(bounds=bounds)
