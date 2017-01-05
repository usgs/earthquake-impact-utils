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

        :returns:
          Tuple of (authoritative event ID, all other IDs associated with event)
        """
        allids = self._jdict['properties']['ids'].strip(',').split(',')
        authid = self._jdict['id']
        allids.remove(authid)
        return (authid,allids)

    def getAssociatedSources(self):
        """Query ComCat for the event sources associated with input ID.

        The output list of other sources is guaranteed to correspond to the 
        list of other ids, and the authoritative source is guaranteed to 
        correspond with the authoritative ID.
        
        :returns:
          Tuple of (authoritative event source, all other sources associated with event)
        """
        #worst case scenario:
        # authid = 'at1234'
        # allids = ['atlas4567','ci2008']
        # allsources = ['atlas','ci','at']
        
        allsources = self._jdict['properties']['sources'].strip(',').split(',')
        authid,allids = self.getAssociatedIds()
        newsources = []
        for eid in [authid] + allids:
            slengths = []
            for source in allsources:
                if eid.startswith(source):
                    slengths.append(len(source))
                else:
                    slengths.append(0)
            newsources.append(allsources[slengths.index(max(slengths))])

        authsource = newsources[0]
        newsources.remove(authsource)
        return (authsource,newsources)

    def getLocation(self):
        """Query ComCat for the location string associated with input ID.

        :returns:
          Location string (i.e. "24km NE of Dharchula, India")
        """
        location = self._jdict['properties']['place']
        return location

    def getTsunami(self):
        """Query ComCat for the location string associated with input ID.

        :returns:
          Location string (i.e. "24km NE of Dharchula, India")
        """
        tsunami = self._jdict['properties']['tsunami']
        return tsunami

    def getURL(self):
        """Query ComCat for the URL associated with input ID.

        :returns:
          Event URL, i.e http://earthquake.usgs.gov/earthquakes/eventpage/us20007z80
        """
        url = self._jdict['properties']['url']
        return url
