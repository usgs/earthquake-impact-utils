#!/usr/bin/env python

# stdlib imports
from cartopy.mpl.geoaxes import GeoAxes
import cartopy.crs as ccrs  # projections
import matplotlib
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import numpy as np
import os.path
import sys

# local imports
from impactutils.mapping.scalebar import draw_scale

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
impactdir = os.path.abspath(os.path.join(homedir, '..', '..'))
# put this at the front of the system path, ignoring any installed impact stuff
sys.path.insert(0, impactdir)


def test_draw_scale():
    fig = plt.figure(figsize=(4, 4))
    proj = ccrs.AlbersEqualArea(central_latitude=30,
                                central_longitude=-82.5,
                                standard_parallels=(30.0))
    ax = fig.add_axes([0, 0, 1, 1], projection=proj,)
    ax.coastlines()
    ax.set_extent([-90, -75, 25, 35])
    draw_scale(ax, pos='ll', units='m')


if __name__ == '__main__':
    test_draw_scale()
