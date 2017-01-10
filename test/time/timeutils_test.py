#!/usr/bin/env python

#stdlib imports
import os.path
import sys
from datetime import datetime,timedelta
from collections import OrderedDict
from urllib import request
import tempfile
import shutil

#third party libraries
import bs4

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
impactdir = os.path.abspath(os.path.join(homedir,'..','..'))
sys.path.insert(0,impactdir) #put this at the front of the system path, ignoring any installed impact stuff

from impactutils.time.timeutils import LocalTime,ElapsedTime,get_recent_timezone_data

def local_time_test():
    tdir = None
    try:
        tdir = tempfile.mkdtemp()
        shpfile = get_recent_timezone_data(tdir)

        standard_offsets = OrderedDict([('Manhattan',(40.7831, -73.9712,-5)),
                                        ('Denver',(39.704545,-104.941406,-7)),
                                        ('LA',(33.864714,-118.212891,-8))])
        utctime = datetime(2016,1,1,20,23,00)
        ltime = None
        for key,value in standard_offsets.items():
            lat,lon,cmpoffset = value
            t1 = datetime.now()
            if ltime is None:
                ltime = LocalTime(shpfile,utctime,lat,lon)
            else:
                ltime.update(utctime,lat,lon)
            t2 = datetime.now()
            dt = t2 - t1
            print('Testing standard time offset for %s' % key)
            localtime = ltime.getLocalTime()
            seconds = dt.seconds + dt.microseconds/1e6
            cmptime = utctime + timedelta(hours=cmpoffset)
            assert localtime == cmptime
            print('Time offset correct - %.1f seconds.' % seconds)

        dst_offsets = OrderedDict([('Manhattan',(40.7831, -73.9712,-4)),
                                   ('Denver',(39.704545,-104.941406,-6)),
                                   ('Phoenix',(33.421556,-112.06604,-7)),
                                   ('LA',(33.864714,-118.212891,-7))])

        utctime = datetime(2016,8,1,20,23,00)
        ltime = None
        for key,value in dst_offsets.items():
            print('Testing DST time offset for %s' % key)
            lat,lon,cmpoffset = value
            t1 = datetime.now()
            if ltime is None:
                ltime = LocalTime(shpfile,utctime,lat,lon)
            else:
                ltime.update(utctime,lat,lon)
            t2 = datetime.now()
            dt = t2 - t1
            localtime = ltime.getLocalTime()
            seconds = dt.seconds + dt.microseconds/1e6
            cmptime = utctime + timedelta(hours=cmpoffset)
            assert localtime == cmptime
            print('Time offset correct - %.1f seconds.' % seconds)
    except Exception as e:
        raise Exception('Could not run local_time_test: "%s"' % str(e))
    finally:
        if tdir is not None:
            shutil.rmtree(tdir)

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
    local_time_test()
    elapsed_test()
    
    

