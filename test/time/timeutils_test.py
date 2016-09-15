#!/usr/bin/env python

#stdlib imports
import os.path
import sys
from collections import OrderedDict
from datetime import datetime,timedelta

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
impactdir = os.path.abspath(os.path.join(homedir,'..','..'))
sys.path.insert(0,impactdir) #put this at the front of the system path, ignoring any installed impact stuff

from impactutils.time.timeutils import get_local_time,ElapsedTime

def local_time_test():
    offsets = {'Manhattan':(40.7831, -73.9712,-5),
               'Denver':(39.704545,-104.941406,-7),
               'LA':(33.864714,-118.212891,-8)}

    utctime = datetime(2016,1,1,20,23,00)
    for key,value in offsets.items():
        lat,lon,cmpoffset = value
        localtime = get_local_time(utctime,lat,lon)
        cmptime = utctime + timedelta(hours=cmpoffset)
        print('Testing time offset for %s' % key)
        assert localtime == cmptime
        print('Time offset correct.')

def elapsed_test():
    etime = ElapsedTime()
    time1 = datetime(2016,1,1,1,1,1)
    dtimes = OrderedDict([(1,'1 second'),
                          (10,'10 seconds'),
                          (61,'1 minute, 1 second'),
                          (3661,'1 hour, 1 minute'),
                          (86401,'1 day, 0 hours'),
                          (90000,'1 day, 1 hour'),
                          (86400+14582,'1 day, 4 hours'),
                          (86400*2+3601,'2 days, 1 hour'),
                          (86400*8,'1 week, 1 day'),
                          ])
    for nsec,compstr in dtimes.items():
        time2 = time1 + timedelta(seconds=nsec)
        estr = etime.getElapsedString(time1,time2)
        print('%s == %s' % (compstr,estr))
        assert compstr == estr

if __name__ == '__main__':
    elapsed_test()
    local_time_test()
    
