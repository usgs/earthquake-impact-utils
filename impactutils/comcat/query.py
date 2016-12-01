#stdlib imports
from urllib import request
import json

URL_TEMPLATE = 'http://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/[EVENTID].geojson'

def get_associated_ids(eventid):
    """Query ComCat for the event IDs associated with input ID.

    :param eventid:
      Input eventid to be passed to ComCat.
    :returns:
      Tuple of (authoritative event ID, all other IDS associated with event) or (None,None) 
      if url cannot be reached.
    """
    url = URL_TEMPLATE.replace('[EVENTID]',eventid)
    try:
        fh = request.urlopen(url)
        data = fh.read().decode('utf-8')
        fh.close()
        jdict = json.loads(data)
        allids = jdict['properties']['ids'].strip(',').split(',')
        authid = jdict['id']
        allids.remove(authid)
    except:
        authid = None
    return (authid,allids)

def get_location(eventid):
    """Query ComCat for the location string associated with input ID.

    :param eventid:
      Input eventid to be passed to ComCat.
    :returns:
      Location string (i.e. "24km NE of Dharchula, India")
    """
    url = URL_TEMPLATE.replace('[EVENTID]',eventid)
    fh = request.urlopen(url)
    data = fh.read().decode('utf-8')
    fh.close()
    jdict = json.loads(data)
    location = jdict['properties']['place']
    return location
    
