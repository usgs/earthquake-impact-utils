#!/usr/bin/env python

# stdlib imports
import tempfile
import os.path
import shutil

# third party imports
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import ListedColormap

# local imports
from impactutils.colors.cpalette import ColorPalette


TEST_FILE = """#This file is a test file for ColorPalette.
# Lines beginning with pound signs are comments.
# Lines beginning with pound signs followed by a "$" are variable definition lines.
# For example, the following line defines a variable called nan_color.
#$nan_color: 0,0,0,0
#$name: test
Z0 R0  G0  B0  Z1  R1  G1  B1
0   0   0   0   1  85  85  85
1  85  85  85   2 170 170 170
2 170 170 170   3 255 255 255
"""

TEST_DICT = {'red': [(0.0, -0.999, 0.0),
                     (0.33333333333333331, 0.3333333333333333, 0.3333333333333333),
                     (0.66666666666666663, 0.6666666666666666, 0.6666666666666666),
                     (1.0, 1.0, 0.999)],
             'green': [(0.0, -0.999, 0.0),
                       (0.33333333333333331, 0.3333333333333333, 0.3333333333333333),
                       (0.66666666666666663, 0.6666666666666666, 0.6666666666666666),
                       (1.0, 1.0, 0.999)],
             'blue': [(0.0, -0.999, 0.0),
                      (0.33333333333333331, 0.3333333333333333, 0.3333333333333333),
                      (0.66666666666666663, 0.6666666666666666, 0.6666666666666666),
                      (1.0, 1.0, 0.999)]}


def test_simplemap():
    z0 = [0, 1, 2]
    z1 = [1, 2, 3]
    rgb0 = [(0, 0, 0),
            (85, 85, 85),
            (170, 170, 170)]
    rgb1 = [(85, 85, 85),
            (170, 170, 170),
            (255, 255, 255)]
    nan_color = (0, 0, 0, 0)
    cp = ColorPalette('test', z0, z1, rgb0, rgb1, nan_color=nan_color)
    assert cp.getDataColor(0.5) == (0.16470588235294117,
                                    0.16470588235294117, 0.16470588235294117, 1.0)
    cp.vmin = -1.0
    cp.vmax = 4.0
    assert cp.getDataColor(0.5) == (0.29803921568627451,
                                    0.29803921568627451, 0.29803921568627451, 1.0)
    assert cp.getDataColor(0.5, '255') == (76, 76, 76, 255)
    assert cp.getDataColor(0.5, 'hex') == ('#4C4C4C')
    assert cp._cdict == TEST_DICT


def test_presets():
    palettes = ColorPalette.getPresets()
    palettes.sort()
    assert palettes == ['mmi', 'pop', 'shaketopo']

    pop = ColorPalette.fromPreset('pop')
    values = [(0, 1.0),
              (5, 0.749),
              (50, 0.623),
              (100, 0.498),
              (500, 0.372),
              (1000, 0.247),
              (5000, 0.1215),
              (10000, 0.0)]
    for value in values:
        zvalue = value[0]
        expected_red = value[1]
        red = pop.getDataColor(zvalue)[0]
        np.testing.assert_almost_equal(expected_red, red, decimal=2)
    assert pop.vmin == 0
    assert pop.vmax == 50000

    mmi = ColorPalette.fromPreset('mmi')
    values = [(0.5, 1.0),
              (1.5, 0.874)]
    for value in values:
        zvalue = value[0]
        expected_red = value[1]
        red = mmi.getDataColor(zvalue)[0]
        np.testing.assert_almost_equal(expected_red, red, decimal=2)
    assert mmi.vmin == 0
    assert mmi.vmax == 10

    topo = ColorPalette.fromPreset('shaketopo')
    assert topo.vmin == -100
    assert topo.vmax == 9200


def test_colormap():
    viridis = plt.get_cmap('viridis')
    cmap = ColorPalette.fromColorMap('viridis',
                                     np.arange(0, 10),
                                     np.arange(1, 11),
                                     viridis)
    zero_value = np.array([0.26666666666666666,
                           0.00392156862745098,
                           0.32941176470588235,
                           1.0])
    ten_value = np.array([0.9921568627450981,
                          0.9058823529411765,
                          0.1450980392156863,
                          1.0])
    np.testing.assert_almost_equal(cmap.getDataColor(0), zero_value)
    np.testing.assert_almost_equal(cmap.getDataColor(10), ten_value)

    viridis = plt.get_cmap('viridis')
    cmap = ColorPalette.fromColorMap('viridis',
                                     np.arange(-4, 5),
                                     np.arange(-3, 6),
                                     viridis,
                                     is_log=True)
    dcolor = cmap.getDataColor(np.exp(-4.0))
    tcolor = np.array((0.26666666666666666,
                       0.00392156862745098,
                       0.32941176470588235,
                       1.0))
    np.testing.assert_almost_equal(dcolor, tcolor)


def test_file():
    try:
        tdir = tempfile.mkdtemp()
        tfile = os.path.join(tdir, 'test.cpt')
        f = open(tfile, 'wt')
        f.write(TEST_FILE)
        f.close()
        cp = ColorPalette.fromFile(tfile)
        assert cp._cdict == TEST_DICT
    except:
        pass
    finally:
        if os.path.isdir(tdir):
            shutil.rmtree(tdir)


def test_cpt():
    rm = 100  # number of lines to remove on black end of magma_r
    # how much at the zero end should be *just* white before transitioning to
    # meet colors
    ad = 50
    magma_cpt = cm.get_cmap('magma_r', 512)  # start with magma_r
    white_bit = np.array([255 / 256, 250 / 256, 250 / 256, 1]
                         )  # create array of white
    slip_cpt = magma_cpt(np.linspace(0, 1, 512))  # initialize slip_cpt
    # move beginning up to remove black end
    slip_cpt[rm:, :] = slip_cpt[0:-rm, :]
    # gradient from white to beginning of new magma
    r_s = np.linspace(white_bit[0], slip_cpt[rm][0], rm - ad)
    g_s = np.linspace(white_bit[1], slip_cpt[rm][1], rm - ad)
    b_s = np.linspace(white_bit[2], slip_cpt[rm][2], rm - ad)
    slip_cpt[ad:rm, :][:, 0] = r_s
    slip_cpt[ad:rm, :][:, 1] = g_s
    slip_cpt[ad:rm, :][:, 2] = b_s
    slip_cpt[:ad, :] = white_bit
    slipmap = ListedColormap(slip_cpt)
    z0 = np.arange(0, 300, 1)
    z1 = np.arange(1, 301, 1)
    ncolors = 64
    resolution = (z1.max() - z0.min()) / ncolors
    name = 'test'
    cpt = ColorPalette.fromColorMap(name, z0, z1,
                                    slipmap, resolution=resolution)
    try:
        tdir = tempfile.mkdtemp()
        tfile = os.path.join(tdir, 'test.cpt')
        cpt.write(tfile)
        cpt2 = ColorPalette.fromFile(tfile)
        np.testing.assert_almost_equal(cpt.getDataColor(150)[0],
                                       cpt2.getDataColor(150)[0])
    except:
        pass
    finally:
        if os.path.isdir(tdir):
            shutil.rmtree(tdir)


if __name__ == '__main__':
    test_cpt()
    test_presets()
    test_simplemap()
    test_file()
    test_colormap()
