from datetime import datetime,timedelta

def get_local_time(utctime,lat,lon):
    """Return local datetime object given UTC time and a lat/lon.

    NB: This function is currently not aware of daylight savings time.
    
    :param utctime:
      Python datetime object in UTC.
    :param lat:
      Latitude where local time is to be determined.
    :param lon:
      Longitude where local time is to be determined.
    :returns:
      Local datetime object.
    """
    doffset = round(lon/15)
    ltime = utctime + timedelta(seconds=doffset*3600)
    return ltime
