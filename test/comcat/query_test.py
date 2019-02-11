#!/usr/bin/env python

# stdlib imports
import urllib.request as request
import tempfile
import os.path
import sys
from datetime import datetime

# third party imports
import numpy as np

# local imports
from impactutils.comcat.query import ComCatInfo, GeoServe


def test_geoserve():
    positions = [{'name': 'california', 'coords': (37.28935, -119.53125), 'source': 'NC', 'type': 'anss', 
    'place':'Oakhurst', 'region':'Central California'},
                 {'name': 'alaska', 'coords': (
                     63.379217, -151.699219), 'source': 'AK', 'type': 'anss', 'place':'Healy', 'region':'Central Alaska'},
                 {'name': 'aleutians', 'coords': (
                     53.209322, -167.34375), 'source': 'US', 'type': 'NA', 'place':'Unalaska', 'region':'Fox Islands, Aleutian Islands, Alaska'},
                 {'name': 'japan', 'coords': (36.700907, 138.999023), 'source': 'US', 'type': 'NA', 'place':'Numata', 'region':'eastern Honshu, Japan'}]


    for pdict in positions:
        lat, lon = pdict['coords']
        psource = pdict['source']
        ptype = pdict['type']
        pname = pdict['name']
        place = pdict['place']
        region = pdict['region']
        print('Testing %s authoritative region...' % pname)
        gs = GeoServe(lat, lon)
        authsrc, authtype = gs.getAuthoritative()
        assert authsrc == psource
        assert authtype == ptype
        places = gs.getPlaces()
        regdict = gs.getRegions()
        assert places[0]['properties']['name'] == place
        assert regdict['fe']['features'][0]['properties']['name'] == region
    x = 1


def test_cc():
    eventids = {'ci37374687': ['us200063en', 'nc72648731', 'at00o8jqfp'],
                'nc72672610': ['at00oboavh', 'us10006chu'],
                'ci37528064': ['at00o30yrz', 'nc72596550', 'us10004s7r'],
                'nc72592670': ['us200050nt', 'nn00531804']}

    for eventid, cmp_allids in eventids.items():
        print(eventid)
        ccinfo = ComCatInfo(eventid)
        authid, allids = ccinfo.getAssociatedIds()
        authsource, othersources = ccinfo.getAssociatedSources()
        assert authid == eventid
        for cmpid in cmp_allids:
            assert cmpid in allids

    non_auth_ids = {'us200063en': 'ci37374687',
                    'at00oboavh': 'nc72672610',
                    'at00o30yrz': 'ci37528064',
                    'us200050nt': 'nc72592670'}
    for eventid, cmp_authid in non_auth_ids.items():
        print(eventid)
        ccinfo = ComCatInfo(eventid)
        authid, allids = ccinfo.getAssociatedIds()
        assert cmp_authid == authid

    # test the location function
    cmpstr = 'off the east coast of Honshu, Japan'
    eventid = 'usp000hvpg'
    ccinfo = ComCatInfo(eventid)
    locstr = ccinfo.getLocation()
    assert locstr == cmpstr

    # test the tsunami function
    eventid = 'us1000778i'
    ccinfo = ComCatInfo(eventid)
    cmptsu = 1
    tsunami = ccinfo.getTsunami()
    assert cmptsu == tsunami

    # test the url method
    eventid = 'us1000778i'
    ccinfo = ComCatInfo(eventid)
    cmpurl = 'https://earthquake.usgs.gov/earthquakes/eventpage/us1000778i'
    url = ccinfo.getURL()
    assert cmpurl == url

    # test the getEventParams method
    eventid = 'us1000778i'
    ccinfo = ComCatInfo(eventid)
    cmpdict = {'lat': -42.7373,
               'lon': 173.054,
               'depth': 15.11,
               'magnitude': 7.8,
               'time': datetime(2016, 11, 13, 11, 2, 56)}
    edict = ccinfo.getEventParams()
    assert edict == cmpdict

    # test getAssociatedSources method
    sources = {'ci37374687': ('ci', ['us', 'nc', 'at']),
               'nc72672610': ('nc', ['at', 'us']),
               'ci37528064': ('ci', ['at', 'nc', 'us', 'gcmt']),
               'nc72592670': ('nc', ['us', 'nn', 'gcmt'])}
    for eid, src_tuple in sources.items():
        authsrc, othersrc = src_tuple
        ccinfo = ComCatInfo(eid)
        authsource, othersources = ccinfo.getAssociatedSources()
        assert authsource == authsrc
        assert set(othersources) >= set(othersrc)


if __name__ == '__main__':
    test_geoserve()
    test_cc()
    
