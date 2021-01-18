#!/usr/bin/env python

# stdlib imports
from collections import OrderedDict
from datetime import datetime, timedelta
import os.path
import shutil
import sys
import tempfile

# local imports
from impactutils.time.timeutils import (LocalTime, ElapsedTime,
                                        TimeConversion,
                                        LocalTimeNE,
                                        get_recent_timezone_data)

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
impactdir = os.path.abspath(os.path.join(homedir, '..'))
# put this at the front of the system path, ignoring any installed impact stuff
sys.path.insert(0, impactdir)


def test_time_conversion():
    # test major cities in the world
    top_cities = [[34.6937, 135.5023], [23.8103, 90.4125], [39.9042, 116.4074],
                  [19.0760, 72.8777], [30.0444, 31.2357], [19.4326, -99.1332],
                  [-23.5505, -46.6333], [31.2304, 121.4737], [28.7041, 77.1025],
                  [35.6762, 139.6503]]
    # target codes come from the results of the shapefile
    target_codes = ["Asia/Tokyo",
                    "Asia/Dhaka",
                    "Asia/Shanghai",
                    "Asia/Kolkata",
                    "Africa/Cairo",
                    "America/Mexico_City",
                    "America/Sao_Paulo",
                    "Asia/Shanghai",
                    "Asia/Kolkata",
                    "Asia/Tokyo"]
    conv = TimeConversion()
    for city, tc in zip(top_cities, target_codes):
        code = conv.get_timezone_code(
            city[0], city[1], rounding_method='floor')
        assert code == tc
        code = conv.get_timezone_code(
            city[0], city[1], rounding_method='ceil')
        assert code == tc
        code = conv.get_timezone_code(
            city[0], city[1], rounding_method='round')
        assert code == tc

    # test cities on boundaries
    test_lat = [-5.102776, -5.103354, -2.621489, -2.621717, -9.126894,
                -9.126889, 28.368768, 28.368764, 48.323449, 48.321868,
                -9.841676, -9.808499, 37.134387, 37.132393, 37.30294,
                37.302917, 64.388846, 64.388844, 64.389627, 64.389627,
                33.982931, 33.981760, 34.009354, 34.011024, 34.091925,
                34.092547, 34.102572, 34.102704, 34.114124, 34.114250]
    test_lon = [140.999419, 141.000164, 141.000097, 140.999780, 141.019556,
                141.019564, -8.667612, -8.667606, 85.673329, 85.701865,
                -50.527084, -50.523313, -114.025281, -114.063424, -114.051763,
                -114.051539, -141.001309, -141.001302, -141.001291, -141.001320,
                -103.081315, -103.014956, -103.061549, -103.028369, -103.046212,
                -103.039999, -103.043792, -103.043223, -103.049971, -103.042123]
    target_codes = ["Asia/Jayapura",
                    "Asia/Jayapura",
                    "Asia/Jayapura",
                    "Asia/Jayapura",
                    "Asia/Jayapura",
                    "Asia/Jayapura",
                    "Africa/Algiers",
                    "Africa/Algiers",
                    "Asia/Almaty",
                    "Asia/Shanghai",
                    "America/Cuiaba",
                    "America/Belem",
                    "America/Denver",
                    "America/Los_Angeles",
                    "America/Denver",
                    "America/Denver",
                    "America/Anchorage",
                    "America/Whitehorse",
                    "America/Whitehorse",
                    "America/Anchorage",
                    "America/Denver",
                    "America/Chicago",
                    "America/Denver",
                    "America/Chicago",
                    "America/Denver",
                    "America/Chicago",
                    "America/Denver",
                    "America/Chicago",
                    "America/Denver",
                    "America/Chicago"]
    inconsistent = []
    print('Testing boundaries with floor rounding.')
    for lat, lon, tc in zip(test_lat, test_lon, target_codes):
        code = conv.get_timezone_code(lat, lon, rounding_method='floor')
        if code != tc:
            inconsistent += [(tc, code)]
    print(f"{len(inconsistent)} out of {len(target_codes)} codes inconsistent "
          f"(shapefile, raster): {inconsistent}")
    inconsistent = []
    print('Testing boundaries with ceil rounding.')
    for lat, lon, tc in zip(test_lat, test_lon, target_codes):
        code = conv.get_timezone_code(lat, lon, rounding_method='ceil')
        if code != tc:
            inconsistent += [(tc, code)]
    print(f"{len(inconsistent)} out of {len(target_codes)} codes inconsistent "
          f"(shapefile, raster): {inconsistent}")
    inconsistent = []
    print('Testing boundaries with rounding.')
    for lat, lon, tc in zip(test_lat, test_lon, target_codes):
        code = conv.get_timezone_code(lat, lon, rounding_method='round')
        if code != tc:
            inconsistent += [(tc, code)]
    print(f"{len(inconsistent)} out of {len(target_codes)} codes inconsistent "
          f"(shapefile, raster): {inconsistent}")

    # compare to the LocalTime class
    local_cities = [[-8.470, 30.085],
                    [40.7831, -73.9712],
                    [39.704545, -104.941406],
                    [-18.666, 176.073],
                    [33.864714, -118.212891]]
    target_times = [datetime.strptime("2016-01-01 22:23:00", "%Y-%m-%d %H:%M:%S"),
                    datetime.strptime("2016-01-01 15:23:00",
                                      "%Y-%m-%d %H:%M:%S"),
                    datetime.strptime("2016-01-01 13:23:00",
                                      "%Y-%m-%d %H:%M:%S"),
                    datetime.strptime("2016-01-02 08:23:00",
                                      "%Y-%m-%d %H:%M:%S"),
                    datetime.strptime("2016-01-01 12:23:00", "%Y-%m-%d %H:%M:%S")]
    for city, tt in zip(local_cities, target_times):
        utctime = datetime(2016, 1, 1, 20, 23, 00)
        localtime = conv.to_localtime(utctime, city[0], city[1],
                                      rounding_method='floor')
        assert localtime.day == tt.day
        assert localtime.month == tt.month
        assert localtime.year == tt.year
        assert localtime.hour == tt.hour
        assert localtime.minute == tt.minute
        assert localtime.second == tt.second
        localtime = conv.to_localtime(utctime, city[0], city[1],
                                      rounding_method='round')
        assert localtime.day == tt.day
        assert localtime.month == tt.month
        assert localtime.year == tt.year
        assert localtime.hour == tt.hour
        assert localtime.minute == tt.minute
        assert localtime.second == tt.second
        localtime = conv.to_localtime(utctime, city[0], city[1],
                                      rounding_method='ceil')
        assert localtime.day == tt.day
        assert localtime.month == tt.month
        assert localtime.year == tt.year
        assert localtime.hour == tt.hour
        assert localtime.minute == tt.minute
        assert localtime.second == tt.second

    # compare to the LocalTime class with DST
    local_cities = [[40.7831, -73.9712],
                    [39.704545, -104.941406],
                    [33.421556, -112.06604],
                    [33.864714, -118.212891]]
    target_times = [datetime.strptime("2016-08-01 16:23:00", "%Y-%m-%d %H:%M:%S"),
                    datetime.strptime("2016-08-01 14:23:00",
                                      "%Y-%m-%d %H:%M:%S"),
                    datetime.strptime("2016-08-01 13:23:00",
                                      "%Y-%m-%d %H:%M:%S"),
                    datetime.strptime("2016-08-01 13:23:00",
                                      "%Y-%m-%d %H:%M:%S")]
    for city, tt in zip(local_cities, target_times):
        utctime = datetime(2016, 8, 1, 20, 23, 00)
        localtime = conv.to_localtime(utctime, city[0], city[1],
                                      rounding_method='floor')
        assert localtime.day == tt.day
        assert localtime.month == tt.month
        assert localtime.year == tt.year
        assert localtime.hour == tt.hour
        assert localtime.minute == tt.minute
        assert localtime.second == tt.second
        localtime = conv.to_localtime(utctime, city[0], city[1],
                                      rounding_method='round')
        assert localtime.day == tt.day
        assert localtime.month == tt.month
        assert localtime.year == tt.year
        assert localtime.hour == tt.hour
        assert localtime.minute == tt.minute
        assert localtime.second == tt.second
        localtime = conv.to_localtime(utctime, city[0], city[1],
                                      rounding_method='ceil')
        assert localtime.day == tt.day
        assert localtime.month == tt.month
        assert localtime.year == tt.year
        assert localtime.hour == tt.hour
        assert localtime.minute == tt.minute
        assert localtime.second == tt.second

    # Converting local time to UTC
    local_cities = [[40.7831, -73.9712],
                    [39.704545, -104.941406],
                    [33.421556, -112.06604],
                    [33.864714, -118.212891]]
    local_times = [datetime.strptime("2016-08-01 16:23:00", "%Y-%m-%d %H:%M:%S"),
                   datetime.strptime("2016-08-01 14:23:00",
                                     "%Y-%m-%d %H:%M:%S"),
                   datetime.strptime("2016-08-01 13:23:00",
                                     "%Y-%m-%d %H:%M:%S"),
                   datetime.strptime("2016-08-01 13:23:00",
                                     "%Y-%m-%d %H:%M:%S")]
    target_time = datetime(2016, 8, 1, 20, 23, 00)
    for city, lt in zip(local_cities, local_times):
        utctime = conv.to_utctime(lt, city[0], city[1],
                                  rounding_method='floor')
        assert utctime.day == target_time.day
        assert utctime.month == target_time.month
        assert utctime.year == target_time.year
        assert utctime.hour == target_time.hour
        assert utctime.minute == target_time.minute
        assert utctime.second == target_time.second
        utctime = conv.to_utctime(lt, city[0], city[1],
                                  rounding_method='ceil')
        assert utctime.day == target_time.day
        assert utctime.month == target_time.month
        assert utctime.year == target_time.year
        assert utctime.hour == target_time.hour
        assert utctime.minute == target_time.minute
        assert utctime.second == target_time.second
        utctime = conv.to_utctime(lt, city[0], city[1],
                                  rounding_method='round')
        assert utctime.day == target_time.day
        assert utctime.month == target_time.month
        assert utctime.year == target_time.year
        assert utctime.hour == target_time.hour
        assert utctime.minute == target_time.minute
        assert utctime.second == target_time.second

    # Check for error with added shapefile
    # Check for all missing arguments
    failed = False
    try:
        conv = TimeConversion(tiff="sample tiff")
    except Exception:
        failed = True
    assert failed == True

    # Check for all missing raster shape
    failed = False
    try:
        conv = TimeConversion("sample tiff",
                              extents={}, resolution=(0.1, 0.1),
                              timezone_coding='jsonfile')
    except Exception:
        failed = True
    assert failed == True

    # Check for all missing raster extent
    failed = False
    try:
        conv = TimeConversion("sample tiff", raster_shape=(1, 2),
                              resolution=(0.1, 0.1), timezone_coding='jsonfile')
    except Exception:
        failed = True
    assert failed == True

    # Check for all missing raster resolution
    failed = False
    try:
        conv = TimeConversion("sample tiff", raster_shape=(1, 2),
                              extents={}, timezone_coding='jsonfile')
    except Exception:
        failed = True
    assert failed == True

    # Check for all missing country code file
    failed = False
    try:
        conv = TimeConversion("sample tiff", raster_shape=(1, 2),
                              extents={}, resolution=(0.1, 0.1))
    except Exception:
        failed = True
    assert failed == True

    # Add test for locations out of the raster extent
    upper = [(85, -49.242448), (85, 95.867115), (-81.164926, -77.917277)]
    target_times = [datetime.strptime("2016-08-01 8:00:00", "%Y-%m-%d %H:%M:%S"),
                    datetime.strptime("2016-08-01 16:00:00",
                                      "%Y-%m-%d %H:%M:%S"),
                    datetime.strptime("2016-08-01 7:00:00",
                                      "%Y-%m-%d %H:%M:%S")]
    for city, tt in zip(upper, target_times):
        utctime = datetime(2016, 8, 1, 10, 00, 00)
        localtime = conv.to_localtime(utctime, city[0], city[1],
                                      rounding_method='floor')
        assert localtime.day == tt.day
        assert localtime.month == tt.month
        assert localtime.year == tt.year
        assert localtime.hour == tt.hour
        assert localtime.minute == tt.minute
        assert localtime.second == tt.second


def _test_local_time(shapefile=None):
    tdir = None
    try:
        tdir = tempfile.mkdtemp()
        if shapefile is None:
            shpfile = get_recent_timezone_data(tdir)
        else:
            shpfile = shapefile

        standard_offsets = OrderedDict([
            ('Zambia', (-8.470, 30.085, 2)),
            ('Manhattan', (40.7831, -73.9712, -5)),
            ('Denver', (39.704545, -104.941406, -7)),
            ('Fiji', (-18.666, 176.073, 12)),
            ('LA', (33.864714, -118.212891, -8))])
        utctime = datetime(2016, 1, 1, 20, 23, 00)
        ltime = None
        for key, value in standard_offsets.items():
            lat, lon, cmpoffset = value
            t1 = datetime.now()
            if ltime is None:
                ltime = LocalTime(shpfile, utctime, lat, lon)
            else:
                ltime.update(utctime, lat, lon)
            t2 = datetime.now()
            dt = t2 - t1
            print(f'Testing standard time offset for {key}')
            localtime = ltime.getLocalTime()
            seconds = dt.seconds + dt.microseconds / 1e6
            cmptime = utctime + timedelta(hours=cmpoffset)
            assert localtime == cmptime
            print(f'Time offset correct - {seconds:.1f} seconds.')

        dst_offsets = OrderedDict([
            ('Manhattan', (40.7831, -73.9712, -4)),
            ('Denver', (39.704545, -104.941406, -6)),
            ('Phoenix', (33.421556, -112.06604, -7)),
            ('LA', (33.864714, -118.212891, -7))])

        utctime = datetime(2016, 8, 1, 20, 23, 00)
        ltime = None
        for key, value in dst_offsets.items():
            print(f'Testing DST time offset for {key}')
            lat, lon, cmpoffset = value
            t1 = datetime.now()
            if ltime is None:
                ltime = LocalTime(shpfile, utctime, lat, lon)
            else:
                ltime.update(utctime, lat, lon)
            t2 = datetime.now()
            dt = t2 - t1
            localtime = ltime.getLocalTime()
            seconds = dt.seconds + dt.microseconds / 1e6
            cmptime = utctime + timedelta(hours=cmpoffset)
            assert localtime == cmptime
            print(f'Time offset correct - {seconds:.1f} seconds.')
    except Exception as e:
        raise Exception(f'Could not run local_time_test: "{str(e)}"')
    finally:
        if tdir is not None:
            shutil.rmtree(tdir)


def test_elapsed():
    etime = ElapsedTime()
    time1 = datetime(2016, 1, 1, 1, 1, 1)
    dtimes = OrderedDict([(1, '1 second'),
                          (10, '10 seconds'),
                          (61, '1 minute, 1 second'),
                          (3661, '1 hour, 1 minute'),
                          (86401, '1 day, 0 hours'),
                          (90000, '1 day, 1 hour'),
                          (86400 + 14582, '1 day, 4 hours'),
                          (86400 * 2 + 3601, '2 days, 1 hour'),
                          (86400 * 8, '1 week, 1 day'),
                          ])
    for nsec, compstr in dtimes.items():
        time2 = time1 + timedelta(seconds=nsec)
        estr = etime.getElapsedString(time1, time2)
        print(f'{compstr} == {estr}')
        assert compstr == estr


def test_local_time_ne():
    utctime = datetime(2021, 1, 8, 0, 28, 49)
    points = {
        'Kermadec Islands': (-29.478, 178.702, 13),
        'New York City': (40.741895, -73.989308, -5),
        'Los Angeles': (33.9074, -118.2704, -8),
        'Capetown': (-33.9196, 18.3302, 2),
        'Antarctic': (-68.1215, 52.7888, 4),
        'Arctic': (83.5622, 7.1719, 0),
        'Southern Ocean': (-61.16, -174.45, -12),
        'Vostok Station': (-78.51, 107.30, 6),
        'Norfolk Island': (-29.0, 168.3, 12),
        'Helsinki': (61.2, 25.5, 2),
        'Kaliningrad': (54.83, 20.94, 2),
    }
    for location, mtuple in points.items():
        lat, lon, offset_hours = mtuple
        dt_offset = timedelta(seconds=3600 * offset_hours)
        print(location)
        ltime = LocalTimeNE(utctime, lat, lon)
        offset = ltime.getUTCOffset()
        assert offset == dt_offset


if __name__ == '__main__':
    test_local_time_ne()
    test_time_conversion()
    if len(sys.argv) > 1:
        shpfile = sys.argv[1]
        _test_local_time(shapefile=shpfile)
    test_elapsed()
