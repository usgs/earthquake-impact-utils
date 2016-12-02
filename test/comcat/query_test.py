#!/usr/bin/env python

#stdlib imports
import urllib.request as request
import tempfile
import os.path
import sys

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
impactdir = os.path.abspath(os.path.join(homedir,'..','..'))
sys.path.insert(0,impactdir) #put this at the front of the system path, ignoring any installed impact stuff

#third party imports
import numpy as np

#local imports
from impactutils.comcat.query import ComCatInfo

def test():
    eventids = {'ci37374687':['us200063en', 'nc72648731', 'at00o8jqfp'],
                'nc72672610':['at00oboavh', 'us10006chu'],
                'ci37528064':['at00o30yrz', 'nc72596550', 'us10004s7r'],
                'nc72592670':['us200050nt', 'nn00531804']}
    
    for eventid,cmp_allids in eventids.items():
        ccinfo = ComCatInfo(eventid)
        authid,allids = ccinfo.getAssociatedIds()
        
        assert authid == eventid
        for cmpid in cmp_allids:
            assert cmpid in allids

    non_auth_ids = {'us200063en':'ci37374687',
                    'at00oboavh':'nc72672610',
                    'at00o30yrz':'ci37528064',
                    'us200050nt':'nc72592670'}
    for eventid,cmp_authid in non_auth_ids.items():
        ccinfo = ComCatInfo(eventid)
        authid,allids = ccinfo.getAssociatedIds()
        assert cmp_authid == authid

    #test the location function
    cmpstr = 'off the east coast of Honshu, Japan'
    eventid = 'usp000hvpg'
    ccinfo = ComCatInfo(eventid)
    locstr = ccinfo.getLocation()
    assert locstr == cmpstr

    #test the tsunami function
    eventid = 'us1000778i'
    ccinfo = ComCatInfo(eventid)
    cmptsu = 1
    tsunami = ccinfo.getTsunami()
    assert cmptsu == tsunami
        
if __name__ == '__main__':
    test()
