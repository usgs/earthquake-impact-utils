#!/usr/bin/env python

from __future__ import print_function

#stdlib imports
import os.path
import sys

import pyproj
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import cartopy.crs as ccrs  # projections

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
mapiodir = os.path.abspath(os.path.join(homedir,'..','..'))
sys.path.insert(0,mapiodir) #put this at the front of the system path, ignoring any installed mapio stuff

from impactutils.mapping.cartopycity import CartopyCities

matplotlib.use('Agg')

def get_two_figures(bounds,figsize):
    xmin,xmax,ymin,ymax = bounds
    clon = (xmin + xmax)/2
    clat = (ymin + ymax)/2
    proj = ccrs.Mercator(central_longitude=clon,
                         min_latitude=ymin,
                         max_latitude=ymax,
                         globe=None)
    geoproj = ccrs.PlateCarree()
    
    # set up an axes object
    fig1 = plt.figure(figsize=figsize)
    ax1 = fig1.add_axes([0,0,1,1],projection=proj)
    ax1.set_extent([xmin, xmax, ymin, ymax],crs=geoproj)

    # set up an identical axes object
    fig2 = plt.figure(figsize=figsize)
    ax2 = fig2.add_axes([0,0,1,1],projection=proj)
    ax2.set_extent([xmin, xmax, ymin, ymax],crs=geoproj)

    return (fig1,ax1,fig2,ax2)

    

def test():
    cityfile = os.path.join(homedir,'data','cities1000.txt')
    print('Test loading geonames cities file...')
    cities = CartopyCities.fromDefault() #load from the web
    print('Passed loading geonames cities file.')

    print('Test limiting cities using California bounds...')
    ymin,ymax = 32.394, 42.062
    xmin,xmax = -125.032, -114.002
    xmin,ymin,xmax,ymax = -121.046000,32.143500,-116.046000,36.278500
    bcities = cities.limitByBounds((xmin,xmax,ymin,ymax))
    print('Done limiting cities using California bounds.')

    print('Test removing cities with collisions...')
    ymin,ymax = 32.394, 42.062
    xmin,xmax = -125.032, -114.002
    # set up you axes object with the projection of interest
    fig1,ax1,fig2,ax2 = get_two_figures((xmin,xmax,ymin,ymax),(8,8))

    #compare the transformation objects of the old and new axes objects
    trans1 = ax1.transData
    invtrans1 = trans1.inverted()
    trans2 = ax2.transData
    invtrans2 = trans2.inverted()
    x1,y1 = (0.5,0.5)
    xdisp1,ydisp1 = trans1.transform((x1,y1))
    x2,y2 = invtrans2.transform((xdisp1,ydisp1))

    fig1.canvas.draw()
    mapcities = bcities.limitByMapCollision(ax1)
    mapcities.renderToMap(ax2)
    #plt.savefig('output.png')
    df = mapcities.getDataFrame()
    boxes = []
    for index,row in df.iterrows():
        left = row['left']
        right = row['right']
        left = row['bottom']
        right = row['top']
        for box in boxes:
            bleft,bright,bbottom,btop = box
            #http://gamedevelopment.tutsplus.com/tutorials/collision-detection-using-the-separating-axis-theorem--gamedev-169
            width = left - bleft
            hw_box1 = (right-left)*0.5
            hw_box2 = (right-left)*0.5
            hgap = length - hw_box1 - hw_box2

            height = top - btop
            hh_box1 = (top-bottom)*0.5
            hh_box2 = (btop-bbottom)*0.5
            vgap = height - hh_box1 - hh_box2
            
            assert hgap > 0 and vgap > 0

    print('Passed test of city collisions...')

    print('Test all supported font names...')
    f = plt.figure()
    ax = f.add_axes([0.1,0.1,0.8,0.8])
    plt.plot(1,1)
    for name in mapcities.getFontList():
        plt.text(1,1,name,fontname=name)
    for name in mapcities.SUGGESTED_FONTS:
        plt.text(1,1,name,fontname=name)
    print('Passed test of supported font names.')
    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        cfile = sys.argv[1]
        test(cityfile=cfile)
    else:
        test()
