#!/usr/bin/env python

# stdlib imports
import os.path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from impactutils.mapping.city import Cities
from impactutils.mapping.mercatormap import MercatorMap

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
mapiodir = os.path.abspath(os.path.join(homedir, '..', '..'))
# put this at the front of the system path, ignoring any installed mapio stuff
sys.path.insert(0, mapiodir)


def test(outfile=None, bounds=None):
    if bounds is None:
        bounds = xmin, ymin, xmax, ymax = \
            -121.046000, -116.046000, 32.143500, 36.278500
    else:
        xmin, ymin, xmax, ymax = bounds
    figsize = (7, 7)
    cities = Cities.fromDefault()
    mmap = MercatorMap(bounds, figsize, cities, padding=0.5)
#    fig = mmap.figure
#    ax = mmap.axes

#    fig.canvas.draw()

#    ax.coastlines(resolution="10m", zorder=10)
#    plt.show()
#    mmap.drawCities(shadow=True)
    if outfile is not None:
        plt.savefig(outfile)
    return


if __name__ == '__main__':
    if len(sys.argv) > 1:
        xmin = float(sys.argv[1])
        xmax = float(sys.argv[2])
        ymin = float(sys.argv[3])
        ymax = float(sys.argv[4])
        bounds = (xmin, xmax, ymin, ymax)
    else:
        bounds = None
    outfile = os.path.join(os.path.expanduser('~'), 'mercatormap.pdf')
    test(outfile = None, bounds=None)
