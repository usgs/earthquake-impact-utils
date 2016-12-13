#stdlib imports
from urllib import request
import json

URL_TEMPLATE = 'http://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/[EVENTID].geojson'

class ComCatInfo(object):
    def __init__(self,eventid):
        url = URL_TEMPLATE.replace('[EVENTID]',eventid)
        try:
            fh = request.urlopen(url)
            data = fh.read().decode('utf-8')
            fh.close()
            self._jdict = json.loads(data)
        except Exception as e:
            raise Exception('Could not connect to ComCat server.').with_traceback(e.__traceback__)

    def getAssociatedIds(self):
        """Query ComCat for the event IDs associated with input ID.

        :param eventid:
          Input eventid to be passed to ComCat.
        :returns:
          Tuple of (authoritative event ID, all other IDS associated with event) or (None,None) 
          if url cannot be reached.
        """
        allids = self._jdict['properties']['ids'].strip(',').split(',')
        authid = self._jdict['id']
        allids.remove(authid)
        return (authid,allids)

    def getLocation(self):
        """Query ComCat for the location string associated with input ID.

        :param eventid:
          Input eventid to be passed to ComCat.
        :returns:
          Location string (i.e. "24km NE of Dharchula, India")
        """
        location = self._jdict['properties']['place']
        return location

    def getTsunami(self):
        """Query ComCat for the location string associated with input ID.

        :param eventid:
          Input eventid to be passed to ComCat.
        :returns:
          Location string (i.e. "24km NE of Dharchula, India")
        """
        tsunami = self._jdict['properties']['tsunami']
        return tsunami

