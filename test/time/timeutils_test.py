#!/usr/bin/env python

#stdlib imports
import os.path
import sys
from datetime import datetime

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
impactdir = os.path.abspath(os.path.join(homedir,'..','..'))
sys.path.insert(0,impactdir) #put this at the front of the system path, ignoring any installed impact stuff

from impactutils.time.timeutils import get_local_time

def test():
    utctime = datetime(2016,1,1,20,23,00)
    cmptime = datetime(2016,1,1,15,23,00)
    lat,lon = 40.7831, -73.9712
    localtime = get_local_time(utctime,lat,lon)
    assert localtime == cmptime

if __name__ == '__main__':
    test()
