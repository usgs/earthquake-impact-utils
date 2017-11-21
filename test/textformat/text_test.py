#!/usr/bin/env python

# stdlib imports
import os.path
import sys

# local imports
from impactutils.textformat import text

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
impactdir = os.path.abspath(os.path.join(homedir, '..', '..'))
# put this at the front of the system path, ignoring any installed impact stuff
sys.path.insert(0, impactdir)


def test():
    print('Testing decimal to roman number conversion...')
    assert text.dec_to_roman(10) == 'X'
    print('Passed decimal to roman number conversion...')

    print('Testing setting number precision...')
    assert text.set_num_precision(7642, 2) == 7600
    print('Passed setting number precision...')

    print('Testing rounding population value...')
    assert text.pop_round(7642) == '8,000'
    print('Passed rounding population value...')

    print('Testing rounding dollar value...')
    assert text.dollar_round(1.234e9, digits=2, mode='short') == '$1.2B'
    assert text.dollar_round(1.234e9, digits=2, mode='long') == '$1.2 billion'
    print('Passed rounding population value...')

    print('Testing abbreviating population value...')
    assert text.pop_round_short(1024125) == '1,024k'
    print('Passed abbreviating population value...')

    print('Testing rounding to nearest integer value...')
    assert text.round_to_nearest(998, round_value=1000) == 1000
    assert text.round_to_nearest(78, round_value=100) == 100
    print('Passed rounding population value...')

    print('Testing flooring to nearest integer value...')
    assert text.floor_to_nearest(1501, floor_value=1000) == 1000
    assert text.floor_to_nearest(51, floor_value=100) == 0
    print('Passed flooring population value...')

    print('Testing ceiling to nearest integer value...')
    assert text.ceil_to_nearest(1001, ceil_value=1000) == 2000
    assert text.ceil_to_nearest(49, ceil_value=100) == 100
    print('Passed ceiling population value...')

    print('Testing commify...')
    assert text.commify(1234567) == '1,234,567'
    print('Passed commify...')

    assert text.floor_to_nearest(0.56, floor_value=0.1) == 0.5
    assert text.ceil_to_nearest(0.44, ceil_value=0.1) == 0.5
    assert text.round_to_nearest(0.48, round_value=0.1) == 0.5
    assert text.pop_round_short(125) == '125'
    assert text.pop_round_short(1.23e6, usemillion=True) == '1m'
    assert text.pop_round_short(0) == '0'
    assert text.dollar_round(1.23, digits=2, mode='short') == '$1'
    assert text.dollar_round(1.23e3, digits=2, mode='short') == '$1.2K'
    assert text.dollar_round(1.23e3, digits=2, mode='long') == '$1.2 thousand'
    assert text.dollar_round(1.23e6, digits=2, mode='short') == '$1.2M'
    assert text.dollar_round(1.23e6, digits=2, mode='long') == '$1.2 million'
    assert text.dec_to_roman(10) == 'X'


if __name__ == '__main__':
    test()
