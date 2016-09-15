#stdlib imports
from datetime import datetime,timedelta
import os.path

#third party imports
import fiona
from shapely.geometry import mapping, shape, Point
from fiona import collection
import pytz

class ElapsedTime(object):
    def __init__(self):
        pass

    def getTimeElapsed(self,time1,time2):
        """Get dictionary containing time values for elapsed time between two input times.

        :param time1:
          Datetime object containing start time.
        :param time2:
          Datetime object containing end time.
        :returns:
          Dictionary containing:
            {'weeks':number of weeks elapsed between time1 and time2,
             'days':number of weeks elapsed between time1 and time2,
             'hours':number of weeks elapsed between time1 and time2,
             'minutes':number of weeks elapsed between time1 and time2,
             'nweeks':number of weeks elapsed between time1 and time2}

        """
        if time2 < time1:
            raise Exception('time2 must be greater than or equal to time1.')
        td = time2 - time1
        nseconds = 0
        nminutes = 0
        nhours = 0
        ndays = 0
        nweeks = 0
        nseconds = td.seconds + td.days*86400
        if nseconds >= 60:
            nminutes = nseconds//60
            nseconds = round(((nseconds/60.0)-nminutes)*60)
            if nminutes >= 60:
                nhours = nminutes//60
                nminutes = round(((nminutes/60.0)-nhours)*60)
                if nhours >= 24:
                    ndays = nhours//24
                    nhours = round(((nhours/24.0)-ndays)*24)
                    if ndays >= 7:
                        nweeks = ndays//7
                        ndays = round(((ndays/7.0)-nweeks)*7)

        results = {'weeks':nweeks,
                   'days':ndays,
                   'hours':nhours,
                   'minutes':nminutes,
                   'seconds':nseconds}
        return results

    def getElapsedString(self,thentime,nowtime=None):
        """Return string describing time elapsed between first input time and now, or first and second input times.
        
        :param thentime: Input datetime object (in the past).
        :param nowtime: Input datetime object (forward in time from thentime).
        :returns: 
          String describing elapsed time in the two longest applicable units of time, up to weeks.
                 '10 minutes, 30 seconds', '10 hours, 47 minutes', '10 days, 23 hours', '2 weeks, 3 days', etc.
        """
        if nowtime is None:
            nowtime = datetime.utcnow()
        etimedict = self.getTimeElapsed(thentime,nowtime)
        if etimedict['weeks']:
            return self.getTimeStr(etimedict['weeks'],etimedict['days'],'week')
        if etimedict['days']:
            return self.getTimeStr(etimedict['days'],etimedict['hours'],'day')
        if etimedict['hours']:
            return self.getTimeStr(etimedict['hours'],etimedict['minutes'],'hour')
        if etimedict['minutes']:
            return self.getTimeStr(etimedict['minutes'],etimedict['seconds'],'minute')
        if etimedict['seconds'] != 1:
            return '%i seconds' % (etimedict['seconds'])
        else:
            return '1 second'

    def getTimeStr(self,bigtime,smalltime,unit):
        """Return a time string describing elapsed time.
        
        :param bigtime:  Number of years, months, days, hours, or minutes.
        :param smalltime: Number of months, days, hours, minutes, or seconds.
        :param unit: String representing the units of bigtime, one of: 'second','minute','hour','day','week'.
        :returns: 
          String elapsed time ('10 days, 13 hours').
        """
        periods = ['second','minute','hour','day','week','month','year']
        if unit not in periods:
            raise Exception('Unknown input units %s' % unit)
        
        bigunit = periods[periods.index(unit)]
        smallunit = periods[periods.index(unit)-1]
        if bigtime != 1:
            bigunit = bigunit+'s'
        if smalltime != 1:
            smallunit = smallunit+'s'
        return '%s %s, %i %s' % (bigtime,bigunit,smalltime,smallunit)
    
def get_local_time(utctime,lat,lon):
    """Return local datetime object given UTC time and a lat/lon.

    Note: This function currently has no knowledge of Daylight Savings Time, 
    so the local times returned will currently only reflect the standard time
    for each zone.
    
    :param utctime:
      Python datetime object in UTC.
    :param lat:
      Latitude where local time is to be determined.
    :param lon:
      Longitude where local time is to be determined.
    :returns:
      Local datetime object.
    """
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    jsonfile = os.path.abspath(os.path.join(homedir,'..','data','timezones.json'))
    ltime = None
    with collection(jsonfile, "r") as input:
        schema = input.schema.copy()
        for f in input:
            zonepoly = shape(f['geometry'])
            timezone = f['properties']['zone']
            hours = int(timezone)
            minutes = int((timezone - hours)*60)
            offset = timedelta(hours=hours,minutes=minutes)
            if zonepoly.contains(Point(lon,lat)):
                ltime = utctime + offset
                break
    if ltime is None:
        doffset = round(lon/15)
        ltime = utctime + timedelta(seconds=doffset*3600)
    return ltime
