#!/usr/bin/env python

from impactutils.mapping.compass import get_compass_dir, get_compass_dir_azimuth
import numpy as np
import pandas as pd


def test_compass():
    angles = [[1.0, ('N', 'North'), ('N', 'North'), ('N', 'North')],
              [23.5, ('N', 'North'), ('NE', 'Northeast'),
               ('NNE', 'North-northeast')],
              [46, ('E', 'East'), ('NE', 'Northeast'), ('NE', 'Northeast')],
              [68.5, ('E', 'East'), ('E', 'East'), ('ENE', 'East-northeast')],
              [91, ('E', 'East'), ('E', 'East'), ('E', 'East')],
              [113.5, ('E', 'East'), ('SE', 'Southeast'),
               ('ESE', 'East-southeast')],
              [136, ('S', 'South'), ('SE', 'Southeast'), ('SE', 'Southeast')],
              [158.5, ('S', 'South'), ('S', 'South'),
               ('SSE', 'South-southeast')],
              [181, ('S', 'South'), ('S', 'South'), ('S', 'South')],
              [203.5, ('S', 'South'), ('SW', 'Southwest'),
               ('SSW', 'South-southwest')],
              [226, ('W', 'West'), ('SW', 'Southwest'), ('SW', 'Southwest')],
              [248.5, ('W', 'West'), ('W', 'West'), ('WSW', 'West-southwest')],
              [271, ('W', 'West'), ('W', 'West'), ('W', 'West')],
              [293.5, ('W', 'West'), ('NW', 'Northwest'),
               ('WNW', 'West-northwest')],
              [316, ('N', 'North'), ('NW', 'Northwest'), ('NW', 'Northwest')],
              [338.5, ('N', 'North'), ('N', 'North'),
               ('NNW', 'North-northwest')],
              ]

    for row in angles:
        angle = row[0]
        print(f"Testing angle {angle:.1f}")

        # test cardinal directions
        short = row[1][0]
        long = row[1][1]
        short_direction = get_compass_dir_azimuth(angle, resolution='cardinal',
                                                  format='short')
        long_direction = get_compass_dir_azimuth(angle,
                                                 resolution='cardinal',
                                                 format='long')
        assert short_direction == short
        assert long_direction == long

        # test intercardinal directions
        short = row[2][0]
        long = row[2][1]
        short_direction = get_compass_dir_azimuth(angle, resolution='intercardinal',
                                                  format='short')
        long_direction = get_compass_dir_azimuth(angle,
                                                 resolution='intercardinal',
                                                 format='long')
        assert short_direction == short
        assert long_direction == long

        # test meteorological directions
        short = row[3][0]
        long = row[3][1]
        short_direction = get_compass_dir_azimuth(angle, resolution='meteorological',
                                                  format='short')
        long_direction = get_compass_dir_azimuth(angle,
                                                 resolution='meteorological',
                                                 format='long')
        assert short_direction == short
        assert long_direction == long

        assert get_compass_dir_azimuth(-45) == 'NW'


if __name__ == '__main__':
    test_compass()
