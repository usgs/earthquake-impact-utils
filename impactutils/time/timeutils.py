# stdlib imports
from collections import OrderedDict
from datetime import datetime, timedelta
from functools import partial
import json
import os.path
from urllib import parse, request
import shutil
import zipfile
import pathlib

# third party imports
import bs4
from fiona import collection
import numpy as np
from PIL import Image
import pyproj
import pytz
from shapely.geometry import shape, Point
from shapely.ops import transform

# local imports
from impactutils.exceptions import RequiredArgumentError, UnsupportedArgumentError


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
    zone = int((np.floor((clon + 180) / 6) % 60) + 1)
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
            seconds_int = int(etimedict['seconds'])
            return f'{seconds_int:d} seconds'
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
            raise Exception(f'Unknown input units {unit}')

        bigunit = periods[periods.index(unit)]
        smallunit = periods[periods.index(unit) - 1]
        if bigtime != 1:
            bigunit = bigunit + 's'
        if smalltime != 1:
            smallunit = smallunit + 's'
        return f'{bigtime} {bigunit}, {int(smalltime):d} {smallunit}'


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
            utmstr = (f'+proj=utm +zone={int(utmzone):d} +ellps=WGS84 +datum=WGS84 '
                      '+units=m +no_defs')
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


class LocalTimeNE(LocalTime):
    def __init__(self, utctime, lat, lon):
        """Create an instance of a LocalTime object using NaturalEarth data.

        Args:
            shpfile: Path to time zones shapefile found on this page:
                https://www.naturalearthdata.com/downloads/10m-cultural-vectors/timezones/
            utctime: Python datetime object in UTC.
            lat: Latitude where local time is to be determined.
            lon: Longitude where local time is to be determined.
        """
        shpfile = (pathlib.Path(__file__).parent / '..' / '..' / 'impactutils' /
                   'data' / 'ne_10m_time_zones.shp').resolve()
        self._input = collection(str(shpfile), 'r')
        self._lat = lat
        self._lon = lon
        self._utctime = utctime
        self._find_time_zone(utctime, lat, lon)

    def _find_time_zone(self, utctime, lat, lon):
        local_time = None
        for f in self._input:
            zonepoly = shape(f['geometry'])
            timezone = f['properties']['tz_name1st']
            # print(f'\tTimezone: {timezone}')
            xmin, ymin, xmax, ymax = zonepoly.bounds
            if (xmax - xmin) > 180:  # xmin is not the left edge
                txmax = xmax
                xmax = xmin
                xmin = txmax
            if xmin > xmax:
                xmin -= 360
            clon = (xmin + xmax) / 2
            hem = ''
            if lat < 0:
                hem = '+south'
            utmzone = _get_utm_zone(clon)
            utmstr = (f'+proj=utm +zone={int(utmzone):d} {hem} '
                      '+ellps=WGS84 +datum=WGS84 +units=m +no_defs')
            geostr = '+proj=longlat +datum=WGS84 +ellps=WGS84'
            projection = partial(
                pyproj.transform,
                pyproj.Proj(geostr),
                pyproj.Proj(utmstr))

            pshape = transform(projection, zonepoly)
            ppoint = transform(projection, Point(lon, lat))
            try:
                is_inside = pshape.contains(ppoint)
            except Exception:
                try:
                    is_inside = zonepoly.contains(Point(lon, lat))
                except Exception:
                    is_inside = False

            if is_inside:
                try:
                    mytz = pytz.timezone(timezone)
                except Exception:
                    timezone = 'undefined'
                if timezone != 'undefined':
                    mytz = pytz.timezone(timezone)
                    utcoffset = mytz.utcoffset(utctime)
                    local_time = utctime + utcoffset
                else:
                    offset_hours = f['properties']['zone']
                    utcoffset = timedelta(seconds=offset_hours * 3600)
                    local_time = utctime + utcoffset
                    timezone = 'undefined'
                break
        if local_time is None:
            # this is effectively nautical time as the ultimate failover.
            utcoffset = round(lon / 15)
            local_time = utctime + timedelta(seconds=utcoffset * 3600)
        self._local_time = local_time
        self._timezone_str = timezone
        self._utcoffset = utcoffset


class TimeConversion(object):
    def __init__(self, tiff=None, raster_shape=None, extents=None,
                 resolution=None, timezone_coding=None):
        """Creates an instance of the TimeConversion object, which
        makes conversions betwen local and UTC time.

        Args:
            tiff (str): Path to a tiff file. The default is a (resolution = 0.02 degree)
                rasterization of the shapefile found here.
                https://github.com/evansiroky/timezone-boundary-builder/releases.
                The default tiff (combined-raster-with-oceans002.tif)
                is located under the data directory.
            raster_shape (tuple): The shape of the raster array. If a tiff other than
                the default is specified, then the shape must also be specified.
                The default is the shape of the default tiff (9000, 18000).
            resolution (tuple): Resolution in degrees (longitude, latitude).
                If a tiff other than the default is specified, then the resolution
                must also be specified. The default is the resolution of the
                default tiff in degrees (0.02, 0.02).
            extents (dict): Dictionary representing the extent of the raster.
                If a tiff other than the default is specified, then the shape
                must also be specified. Default raster extent example:
                    {
                        "Upper Left": (-180., 83.),
                        "Lower Left": (-180., -80.),
                        "Upper Right": (180., 83.),
                        "Lower Right": (180., -80.)
                    }
            timezone_coding (string): Path to a json file with codes that correspond
                to the integer values in the raster. Example:
                    {
                        "Africa/Abidjan": 0,
                        "Africa/Accra": 1,
                        "Africa/Addis_Ababa": 2,
                        "Africa/Algiers": 3,
                        "Africa/Asmara": 4,
                        "Africa/Bamako": 5,
                    }
                If a tiff other than the default is specified, then the country
                coding file must also be specified. The default is the coding
                file located in the data directory: country-time-codes.json
        """
        if tiff is None:
            homedir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.abspath(
                os.path.join(homedir, '..', 'data'))
            combined_tiff = os.path.join(data_dir,
                                         'combined-raster-with-oceans002.tif')
            timezone_coding = os.path.join(data_dir,
                                           'country-time-codes.json')
            with open(timezone_coding, 'r') as json_file:
                self._timezones = json.load(
                    json_file, object_pairs_hook=OrderedDict)
            self._filepath = combined_tiff
            self._shape = (8150, 18000)
            self._resolution = (0.02, 0.02)
            self._extents = {
                "Upper Left": (-180., 83.),
                "Lower Left": (-180., -80.),
                "Upper Right": (180., 83.),
                "Lower Right": (180., -80.)
            }
        else:
            if raster_shape is None:
                raise RequiredArgumentError('For a custom tiff, the shape of the array '
                                            'must be specified as a tuple. Example: (9000, 18000).')
            if extents is None:
                raise RequiredArgumentError('For a custom tiff, the extents '
                                            'must be specified.')
            if resolution is None:
                raise RequiredArgumentError('For a custom tiff, the resolution of the tiff '
                                            'must be specified as a tuple. Example: (0.02, 0.02).')
            if timezone_coding is None:
                raise RequiredArgumentError('For a custom tiff, the path to the country code '
                                            'file must be specified.')
            self._filepath = tiff
            self._shape = raster_shape
            self._resolution = resolution
            self._extents = extents
            with open(timezone_coding, 'r') as json_file:
                self._timezones = json.load(
                    json_file, object_pairs_hook=OrderedDict)
        self._raster = self.read_tiff()

    def get_timezone_code(self, lat, lon, rounding_method='floor'):
        """
        Gets the timezone code for a given latitude/longitude.

        Args:
            lat (float): Latitude.
            lon (float): Longitude.
            rounding_method (string): The rounding method to use, when finding
                the raster cell. The passed string must be one of: 'floor',
                'ceil', 'round'.

        Returns:
            String timezone code.

        Note:
            This method assumes a symmetrical raster. If the raster extent is
            less than the
        """
        # Validate rounding option
        rounding_option = ['floor, ceil, round']
        if rounding_method not in ['floor', 'ceil', 'round']:
            raise UnsupportedArgumentError(f"{rounding_method} is not a valid 'rounding_method'."
                                           f" It must be one of {rounding_option}.")
        # Get the extents of the raster
        min_lon = self._extents['Lower Left'][0]
        max_lon = self._extents['Lower Right'][0]
        min_lat = self._extents['Lower Left'][1]
        max_lat = self._extents['Upper Left'][1]

        # Account for rasters with limited extent
        # If the value is less than or greater than the extent, then set it to
        # the closest boundary
        if lon > max_lon:
            lon = max_lon
        elif lon < min_lon:
            lon = min_lon
        if lat > max_lat:
            lat = max_lat
        elif lat < min_lat:
            lat = min_lat

        # Set the resolution in x (longitude) and y (latitude)
        resx = self._resolution[0]
        resy = self._resolution[1]
        if max_lon < min_lon and lon < min_lon:
            lon += 360
        col = (lon - min_lon) / resx
        row = (max_lat - lat) / resy

        # Round to get the row/col index of the timezone code
        if rounding_method == 'round':
            row = np.round(row).astype(int)
            col = np.round(col).astype(int)
        elif rounding_method == 'floor':
            row = np.floor(row).astype(int)
            col = np.floor(col).astype(int)
        elif rounding_method == 'ceil':
            row = np.ceil(row).astype(int)
            col = np.ceil(col).astype(int)
        if row >= self._shape[0]:
            row = self._shape[0] - 1
        if col >= self._shape[1]:
            col = self._shape[1] - 1
        raster_value = self._raster[row][col]
        # Find the timezone code
        keys = list(self._timezones.keys())
        values = list(self._timezones.values())
        code = keys[np.argwhere(values == raster_value)[0][0]]
        return code

    def read_tiff(self):
        """
        Reads a tiff file.

        Returns:
            ndarray of the raster.
        """
        image = Image.open(self._filepath)
        image_array = np.asarray(image)
        # Reshape to reflect dimensions of the map
        raster = image_array.reshape(self._shape)
        return raster

    def to_localtime(self, utctime, lat, lon, rounding_method='floor'):
        """
        Converts UTC time to local time.

        Args:
            utctime (datetime): Datetime object in utc time.
            lat (float): Latitude
            lon (float): Longitude.
            rounding_method (string): The rounding method to use, when finding
                the raster cell. The passed string must be one of: 'floor',
                'ceil', 'round'.

        Returns:
            Datetime object for the local time.
        """
        code = self.get_timezone_code(lat, lon)
        timezone = pytz.timezone(code)
        local_time = pytz.utc.localize(utctime).astimezone(timezone)
        return local_time

    def to_utctime(self, localtime, lat, lon, rounding_method='floor'):
        """
        Converts local time to UTC time.

        Args:
            localtime (datetime): Datetime object without any associated timezone.
            lat (float): Latitude
            lon (float): Longitude.
            rounding_method (string): The rounding method to use, when finding
                the raster cell. The passed string must be one of: 'floor',
                'ceil', 'round'.

        Returns:
            Datetime object for the UTC time.
        """
        code = self.get_timezone_code(lat, lon)
        timezone = pytz.timezone(code)
        # Set the local timezone information
        local = timezone.localize(localtime)
        # Convert to UTC
        utc = pytz.utc
        utctime = local.astimezone(utc)
        return utctime
