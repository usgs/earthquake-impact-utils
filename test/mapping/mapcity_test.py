#!/usr/bin/env python

from impactutils.mapping.mapcity import MapCities
from impactutils.mapping.city import Cities

def test_mapcity():
    cities = Cities.fromDefault()  # load from a file contained in repo
    df = cities._dataframe
    mapcities = MapCities(df)
    fontlist = mapcities.getFontList()
    assert len(fontlist) > 0
    try:
        mapcities.limitByMapCollision()
    except NotImplementedError as nie:
        assert 1 == 1

if __name__ == '__main__':
    mapcity_test()
