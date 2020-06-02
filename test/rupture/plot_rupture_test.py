#!/usr/bin/env python

# stdlib imports
import os
import time

# local imports
from impactutils.rupture.factory import get_rupture
from impactutils.rupture.origin import Origin
from impactutils.rupture.plotrupture import map_rupture, plot_rupture_wire3d
from impactutils.time.ancient_time import HistoricTime
import matplotlib.pyplot as plt
import numpy as np


def test_plot():
    # Grab an EdgeRupture
    origin = Origin({'id': 'test', 'lat': 0, 'lon': 0, 'depth': 5.0,
                     'mag': 7.0, 'netid': 'us', 'network': '',
                     'locstring': '', 'time':
                     HistoricTime.utcfromtimestamp(time.time())})
    homedir = os.path.dirname(os.path.abspath(__file__))
    file = os.path.join(homedir, 'rupture_data/cascadia.json')
    rup_original = get_rupture(origin, file)

    fig1 = plt.figure()
    ax1 = fig1.add_subplot(111, projection='3d')
    ax1 = plot_rupture_wire3d(rup_original, ax=ax1)
    fig1.canvas.draw()
    wireframe = np.frombuffer(
        fig1.canvas.tostring_rgb(), dtype=np.uint8)
    wireframe_target_file = os.path.join(
        homedir, 'rupture_data/rupture_wire3d_target.txt')
    wireframe_target = np.loadtxt(wireframe_target_file, dtype=np.uint8)
    np.testing.assert_array_equal(wireframe, wireframe_target)

    fig2 = plt.figure()
    ax2 = fig2.add_subplot(111, projection='3d')
    ax2 = map_rupture(rup_original)
    fig2.canvas.draw()
    map = np.frombuffer(fig2.canvas.tostring_rgb(), dtype=np.uint8)
    map_file = os.path.join(homedir, 'rupture_data/map_rupture_target.txt')
    map_target = np.loadtxt(map_file, dtype=np.uint8)
    np.testing.assert_array_equal(map, map_target)


if __name__ == "__main__":
    test_plot()
