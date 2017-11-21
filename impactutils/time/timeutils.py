# stdlib imports
from datetime import datetime, timedelta
import os.path
from functools import partial
import zipfile
from urllib import request
from urllib import parse
import shutil

# third party imports
from shapely.geometry import shape, Point
from fiona import collection
import pyproj
import numpy as np
from shapely.ops import transform
import pytz
import bs4

TIMEFMT = '%Y-%m-%dT%H:%M:%S'
TIMEOUT = 30  # number of seconds to wait for urlopen requests


def get_recent_timezone_data(outdir):
    """
    Args:
        outdir (str): Output directory.

    Returns:
        shapefile of time zone data
    """
    release_url = 'https://github.com/evansiroky/timezone-boundary-builder/releases/latest'
    fh = request.urlopen(release_url, timeout=TIMEOUT)
    html_data = fh.read().decode('utf-8')
    fh.close()
    soup = bs4.BeautifulSoup(html_data, 'html.parser')
    link = None
    for anchor in soup.find_all('a'):
        if 'href' in anchor.attrs:
            link = anchor.attrs['href']
            if link.find('timezones.shapefile.zip') > -1:
                link = parse.urljoin('https://github.com', link)
                break

    if link is None:
        raise Exception('Could not find most recent time zone data set!')

    fh = request.urlopen(link, timeout=TIMEOUT)
    data = fh.read()
    fh.close()
    outfile = os.path.join(outdir, 'timezones.shapefile.zip')
    f = open(outfile, 'wb')
    f.write(data)
    f.close()
    myzip = zipfile.ZipFile(outfile, 'r')
    shpfile = None
    for fpath in myzip.namelist():
        fbase, fname = os.path.split(fpath)
        outfile = os.path.join(outdir, fname)
        actual_outfile = myzip.extract(fpath, path=outdir)
        if actual_outfile != outfile:
            shutil.move(actual_outfile, outfile)

        if fname.endswith('.shp'):
            shpfile = outfile
    tmpdir = os.path.join(outdir, fbase)
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    myzip.close()
    return shpfile


def _get_utm_zone(clon):
    starts = np.arange(-180, 186, 6)
    zone = np.where((clon > starts) < 1)[0].min()
    return zone


class ElapsedTime(object):
    def __init__(self):
        pass

    def getTimeElapsed(self, time1, time2):
        """
        Get dictionary containing time values for elapsed time between two
        input times.

        Args:
            time1: Datetime object containing start time.
            time2: Datetime object containing end time.

        Returns:
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
        nseconds = td.seconds + td.days * 86400
        if nseconds >= 60:
            nminutes = nseconds // 60
            nseconds = round(((nseconds / 60.0) - nminutes) * 60)
            if nminutes >= 60:
                nhours = nminutes // 60
                nminutes = round(((nminutes / 60.0) - nhours) * 60)
                if nhours >= 24:
                    ndays = nhours // 24
                    nhours = round(((nhours / 24.0) - ndays) * 24)
                    if ndays >= 7:
                        nweeks = ndays // 7
                        ndays = round(((ndays / 7.0) - nweeks) * 7)

        results = {'weeks': nweeks,
                   'days': ndays,
                   'hours': nhours,
                   'minutes': nminutes,
                   'seconds': nseconds}
        return results

    def getElapsedString(self, thentime, nowtime=None):
        """
        Return string describing time elapsed between first input time and now,
        or first and second input times.

        Args:
            thentime: Input datetime object (in the past).
            nowtime: Input datetime object (forward in time from thentime).

        Returns:
            String describing elapsed time in the two longest applicable units
            of time, up to weeks. Examples:
            - '10 minutes, 30 seconds',
            - '10 hours, 47 minutes',
            - '10 days, 23 hours',
            - '2 weeks, 3 days', etc.
        """
        if nowtime is None:
            nowtime = datetime.utcnow()
        etimedict = self.getTimeElapsed(thentime, nowtime)
        if etimedict['weeks']:
            return self.getTimeStr(etimedict['weeks'],
                                   etimedict['days'], 'week')
        if etimedict['days']:
            return self.getTimeStr(etimedict['days'],
                                   etimedict['hours'], 'day')
        if etimedict['hours']:
            return self.getTimeStr(etimedict['hours'],
                                   etimedict['minutes'], 'hour')
        if etimedict['minutes']:
            return self.getTimeStr(etimedict['minutes'],
                                   etimedict['seconds'], 'minute')
        if etimedict['seconds'] != 1:
            return '%i seconds' % (etimedict['seconds'])
        else:
            return '1 second'

    def getTimeStr(self, bigtime, smalltime, unit):
        """Return a time string describing elapsed time.

        Args:
            bigtime:  Number of years, months, days, hours, or minutes.
            smalltime: Number of months, days, hours, minutes, or seconds.
            unit: String representing the units of bigtime, one of: 'second',
                'minute','hour','day','week'.

        Returns:
           String elapsed time ('10 days, 13 hours').
        """
        periods = ['second', 'minute', 'hour', 'day', 'week', 'month', 'year']
        if unit not in periods:
            raise Exception('Unknown input units %s' % unit)

        bigunit = periods[periods.index(unit)]
        smallunit = periods[periods.index(unit) - 1]
        if bigtime != 1:
            bigunit = bigunit + 's'
        if smalltime != 1:
            smallunit = smallunit + 's'
        return '%s %s, %i %s' % (bigtime, bigunit, smalltime, smallunit)


class LocalTime(object):
    def __init__(self, shpfile, utctime, lat, lon):
        """Create an instance of a LocalTime object.

        Args:
            shpfile: Path to time zones shapefile found on this page:
                https://github.com/evansiroky/timezone-boundary-builder/releases
            utctime: Python datetime object in UTC.
            lat: Latitude where local time is to be determined.
            lon: Longitude where local time is to be determined.
        """
        self._input = collection(shpfile, 'r')
        self._lat = lat
        self._lon = lon
        self._utctime = utctime
        self._find_time_zone(utctime, lat, lon)

    def _find_time_zone(self, utctime, lat, lon):
        local_time = None
        for f in self._input:
            zonepoly = shape(f['geometry'])

            timezone = f['properties']['tzid']

            xmin, ymin, xmax, ymax = zonepoly.bounds
            clon = (xmin + xmax) / 2
            utmzone = _get_utm_zone(clon)
            utmstr = ('+proj=utm +zone=%i +ellps=WGS84 +datum=WGS84 '
                      '+units=m +no_defs' % utmzone)
            geostr = '+proj=longlat +datum=WGS84 +ellps=WGS84'
            projection = partial(
                pyproj.transform,
                pyproj.Proj(geostr),
                pyproj.Proj(utmstr))

            if lat < ymin or lat > ymax or lon < xmin or lon > xmax:
                continue
            pshape = transform(projection, zonepoly)
            ppoint = transform(projection, Point(lon, lat))
            try:
                is_inside = pshape.contains(ppoint)
            except:
                try:
                    is_inside = zonepoly.contains(Point(lon, lat))
                except:
                    is_inside = False

            if is_inside:
                mytz = pytz.timezone(timezone)
                utcoffset = mytz.utcoffset(utctime)
                local_time = utctime + utcoffset
                break
        if local_time is None:
            # this is effectively nautical time as the ultimate failover.
            utcoffset = round(lon / 15)
            local_time = utctime + timedelta(seconds=utcoffset * 3600)
        self._local_time = local_time
        self._timezone_str = timezone
        self._utcoffset = utcoffset

    def getLocalTime(self):
        """Return local datetime object given UTC time and a lat/lon.

        Returns:
            Local datetime object.
        """
        return self._local_time

    def getUTCOffset(self):
        """Return UTC offset for input time,lat,lon.

        Returns:
            UTC offset, as datetime.timedelta object.
        """
        return self._utcoffset

    def getTimeZone(self):
        return self._timezone

    def update(self, utctime, lat, lon):
        self._lat = lat
        self._lon = lon
        self._utctime = utctime
        self._find_time_zone(utctime, lat, lon)

    def __del__(self):
        self._input.close()
