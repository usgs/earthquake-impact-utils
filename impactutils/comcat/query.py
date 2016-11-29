#stdlib imports
from urllib import request
import json

URL_TEMPLATE = 'http://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/[EVENTID].geojson'

def get_associated_ids(eventid):
    url = URL_TEMPLATE.replace('[EVENTID]',eventid)
    fh = request.urlopen(url)
    data = fh.read().decode('utf-8')
    fh.close()
    jdict = json.loads(data)
    allids = jdict['properties']['ids'].strip(',').split(',')
    authid = jdict['id']
    allids.remove(authid)
    return (authid,allids)
    
