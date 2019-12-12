#!/usr/bin/python

# stdlib imports
import re
from math import floor, ceil

# these two lists serves as building blocks to construct any roman numeral
# just like coin denominations.
# 1000->"M", 900->"CM", 500->"D"...keep on going
decimalDens = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
romanDens = ["M", "CM", "D", "CD", "C", "XC",
             "L", "XL", "X", "IX", "V", "IV", "I"]


def dec_to_roman(dec):
    """Return roman numeral version of Arabic integer numeral (limit 4000).

    Example::
      decToRoman(11) => 'XI'
      decToRoman(1025) => 'MXXV'

    Args:
        dec: Integer Arabic numeral.

    Returns:
        Roman numeral equivalent of input, as string.

    Raises:
        ValueError: When input is negative or greater or equal to 4000.
    """
    if dec <= 0:
        raise ValueError("Input value must be positive")
        # to avoid MMMM
    elif dec >= 4000:
        raise ValueError("Input value must be lower than MMMM(4000)")

    return _dec_to_roman(dec, "", decimalDens, romanDens)


def _dec_to_roman(num, s, decs, romans):
    """
    convert a Decimal number to Roman numeral recursively

    Args:
        num: The decimal number.
        s: The roman numerial string.
        decs: Current list of decimal denomination.
        romans: Current list of roman denomination.

    Returns:
        Roman numeral equivalent of num, as string.
    """
    if decs:
        if (num < decs[0]):
            # deal with the rest denomination
            return _dec_to_roman(num, s, decs[1:], romans[1:])
        else:
            # deduce this denomation till num<desc[0]
            return _dec_to_roman(num - decs[0], s + romans[0], decs, romans)
    else:
        # we run out of denomination, we are done
        return s


def set_num_precision(number, precision, mode='int'):
    """
    Return the input number with N digits of precision.

    Args:
        number: Input value.
        precision: Number of digits of desired precision.

    Returns:
        Input value with 'precision' digits of precision.
    """
    fmt = '{:.%ie}' % (precision - 1)
    value = float(fmt.format(number))
    if mode == 'int':
        return int(value)
    else:
        return value


def pop_round(value):
    """
    Round population value to nearest 1000, return as human readable string
    with commas.

    Example::
      print popRound(9184) => '10,000'

    Args:
        value: Population value to be rounded.

    Returns:
        "Commified" string form of value, rounded to nearest 1000.
    """
    return commify(round_to_nearest(value))


def dollar_round(value, digits=2, mode='short'):
    """Return an abbreviated dollar value.

    Args:
        value: Input integer dollar value (i.e., 1000000).
        mode: 'short' or 'long' (default 'short').
        digits: Number of significant digits (default 2).

    Returns:
        Rounded string version of dollar amount (i.e., $1.0B or $1.0 billion).
    """
    if value < 1e3:
        return '$' + commify(set_num_precision(value, digits))
    suffixdict = {'K': 1e3, 'M': 1e6, 'B': 1e9}
    if mode == 'short':
        if value >= suffixdict['K'] and value < suffixdict['M']:
            dollar_value = set_num_precision(value / 1e3, digits, mode='float')
            return f'${dollar_value}K'
        if value >= suffixdict['M'] and value < suffixdict['B']:
            dollar_value = set_num_precision(value / 1e6, digits, mode='float')
            return f'${dollar_value}M'
        else:
            dollar_value = set_num_precision(value / 1e9, digits, mode='float')
            return f'${dollar_value}B'
    else:
        if value >= suffixdict['K'] and value < suffixdict['M']:
            dollar_value = set_num_precision(value / 1e3, digits, mode='float')
            return (f'${dollar_value} thousand')
        if value > suffixdict['M'] and value < suffixdict['B']:
            dollar_value = set_num_precision(value / 1e6, digits, mode='float')
            return (f'${dollar_value} million')
        else:
            dollar_value = set_num_precision(value / 1e9, digits, mode='float')
            return (f'${dollar_value} billion')


def pop_round_short(value, usemillion=False):
    """
    Return an abbreviated population value (i.e., '1,024k' for 1,024,125,
    '99k' for 99,125, '9k' for 9,125).

    Args:
        value: Population value to be shortened.
        usemillion: If True, values greater than 1 million will be appended
            with 'm'.  Default always appends 'k'.

    Returns:
        String population value with 'k' or 'm' appended (or nothing if 0).
    """
    if value < 1000:
        return str(int(value))
    suffixdict = {'k': 1000, 'm': 1000000}
    if value >= suffixdict['m'] and usemillion:
        suffix = 'm'
    else:
        suffix = 'k'

    roundValue = suffixdict[suffix]
    roundnum = round_to_nearest(value) // roundValue
    if roundnum == 0:
        return str(roundnum)
    else:
        return commify(roundnum) + suffix


def round_to_nearest(value, round_value=1000):
    """Return the value, rounded to nearest round_value (defaults to 1000).

    Args:
        value: Value to be rounded.
        round_value: Number to which the value should be rounded.

    Returns:
        Value rounded to nearest desired integer.
    """
    if round_value < 1:
        ds = str(round_value)
        nd = len(ds) - (ds.find('.') + 1)
        value = value * 10**nd
        round_value = round_value * 10**nd
        value = int(round(float(value) / round_value) * round_value)
        value = float(value) / 10**nd
    else:
        value = int(round(float(value) / round_value) * round_value)

    return value


def floor_to_nearest(value, floor_value=1000):
    """Return the value, floored to nearest floor_value (defaults to 1000).

    Args:
        value: Value to be floored.
        floor_value: Number to which the value should be floored.

    Returns:
        Floored value.
    """
    if floor_value < 1:
        ds = str(floor_value)
        nd = len(ds) - (ds.find('.') + 1)
        value = value * 10**nd
        floor_value = floor_value * 10**nd
        value = int(floor(float(value) / floor_value) * floor_value)
        value = float(value) / 10**nd
    else:
        value = int(floor(float(value) / floor_value) * floor_value)
    return value


def ceil_to_nearest(value, ceil_value=1000):
    """Return the value, ceiled to nearest ceil_value (defaults to 1000).

    Args:
        value: Value to be ceiled.
        ceil_value: Number to which the value should be ceiled.

    Returns:
        Ceiled value.
    """
    if ceil_value < 1:
        ds = str(ceil_value)
        nd = len(ds) - (ds.find('.') + 1)
        value = value * 10**nd
        ceil_value = ceil_value * 10**nd
        value = int(ceil(float(value) / ceil_value) * ceil_value)
        value = float(value) / 10**nd
    else:
        value = int(ceil(float(value) / ceil_value) * ceil_value)
    return value


def commify(num, separator=','):
    """
    Return a string representing the number num with separator inserted for
    every power of 1000.

    commify(1234567) -> '1,234,567'

    Args:
        num: Number to be formatted.
        separator: Separator to be used.

    Returns:
        "Commified" string.
    """
    regex = re.compile(r'^(-?\d+)(\d{3})')
    num = str(num)  # just in case we were passed a numeric value
    more_to_do = 1
    while more_to_do:
        substring = rf'\1{separator}\2'
        (num, more_to_do) = regex.subn(substring, num)
    return num
