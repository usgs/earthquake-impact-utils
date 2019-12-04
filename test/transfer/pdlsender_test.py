#!/usr/bin/env python

# stdlib imports
import os.path
import sys
import tempfile
import urllib.request
import urllib.error
import urllib.parse
import zipfile
import shutil
import io
from distutils import spawn
import textwrap
import datetime
from unittest import mock

# local imports
from impactutils.transfer.pdlsender import PDLSender


def test_send():
    props = {'java': '',
             'jarfile': '',
             'privatekey': '',
             'configfile': '',
             'source': 'ci',
             'type': 'dummy',
             'code': 'ci2015abcd',
             'eventsource': 'us',
             'eventsourcecode': 'us1234abcd'}
    optional_props = {'latitude': 34.123,
                      'longitude': -188.456,
                      'depth': 10.1,
                      'eventtime': datetime.datetime.utcnow(),
                      'magnitude': 5.4}
    product_props = {'maxmmi': 5.4,
                     'time': datetime.datetime.utcnow(),
                     'other': {'name': 'testme'},
                     'testint': 5,
                     'alert': 'yellow'}
    props.update(optional_props)
    thisfile = os.path.abspath(__file__)
    patchfunc = 'impactutils.transfer.pdlsender.get_command_output'
    with mock.patch(patchfunc) as mock_output:
        pdl = PDLSender(properties=props, local_files=[thisfile],
                        product_properties=product_props)
        # error code, stdout, stderr
        mock_output.return_value = (True, b'stuff sent', b'')
        nfiles, send_msg = pdl.send()
        assert 'stuff sent' in send_msg


def test_cancel():
    props = {'java': '',
             'jarfile': '',
             'privatekey': '',
             'configfile': '',
             'source': 'ci',
             'type': 'dummy',
             'code': 'ci2015abcd',
             'testint': 5,
             'eventsource': 'us',
             'eventsourcecode': 'us1234abcd'}
    optional_props = {'latitude': 34.123,
                      'longitude': -188.456,
                      'depth': 10.1,
                      'eventtime': datetime.datetime.utcnow(),
                      'magnitude': 5.4}
    product_props = {'maxmmi': 5.4,
                     'alert': 'yellow'}
    props.update(optional_props)
    thisfile = os.path.abspath(__file__)
    patchfunc = 'impactutils.transfer.pdlsender.get_command_output'
    with mock.patch(patchfunc) as mock_output:
        pdl = PDLSender(properties=props, local_files=[thisfile],
                        product_properties=product_props)
        # error code, stdout, stderr
        mock_output.return_value = (True, b'stuff cancelled', b'')
        stdout = pdl.cancel()
        assert 'cancelled' in stdout.decode('utf-8')


def test_send_fail():
    props = {'java': '',
             'jarfile': '',
             'privatekey': '',
             'configfile': '',
             'source': 'ci',
             'type': 'dummy',
             'code': 'ci2015abcd',
             'eventsource': 'us',
             'eventsourcecode': 'us1234abcd'}
    optional_props = {'latitude': 34.123,
                      'longitude': -188.456,
                      'depth': 10.1,
                      'eventtime': datetime.datetime.utcnow(),
                      'magnitude': 5.4}
    product_props = {'maxmmi': 5.4,
                     'alert': 'yellow'}
    props.update(optional_props)
    thisfile = os.path.abspath(__file__)
    patchfunc = 'impactutils.transfer.pdlsender.get_command_output'
    with mock.patch(patchfunc) as mock_output:
        try:
            # attempt to send two files
            pdl = PDLSender(properties=props,
                            local_files=[thisfile, thisfile],
                            product_properties=product_props)
            # error code, stdout, stderr
            mock_output.return_value = (True, b'stuff cancelled', b'')
            nfiles, sendmsg = pdl.send()
        except Exception as e:
            assert 'may only send' in str(e)

        try:
            # attempt to send two files
            pdl = PDLSender(properties=props,
                            local_files=[thisfile],
                            product_properties=product_props)
            # error code, stdout, stderr
            mock_output.return_value = (False, b'error', b'')
            nfiles, sendmsg = pdl.send()
        except Exception as e:
            assert 'Could not send' in str(e)


def test_cancel_fail():
    props = {'java': '',
             'jarfile': '',
             'privatekey': '',
             'configfile': '',
             'source': 'ci',
             'type': 'dummy',
             'code': 'ci2015abcd',
             'eventsource': 'us',
             'eventsourcecode': 'us1234abcd'}
    optional_props = {'latitude': 34.123,
                      'longitude': -188.456,
                      'depth': 10.1,
                      'eventtime': datetime.datetime.utcnow(),
                      'magnitude': 5.4}
    product_props = {'maxmmi': 5.4,
                     'alert': 'yellow'}
    props.update(optional_props)
    thisfile = os.path.abspath(__file__)
    patchfunc = 'impactutils.transfer.pdlsender.get_command_output'
    with mock.patch(patchfunc) as mock_output:
        try:
            # attempt to send two files
            pdl = PDLSender(properties=props,
                            local_files=[thisfile],
                            product_properties=product_props)
            # error code, stdout, stderr
            mock_output.return_value = (False, b'error', b'')
            _ = pdl.cancel()
        except Exception as e:
            assert 'Could not delete product' in str(e)


if __name__ == '__main__':
    test_send()
    test_cancel()
    test_send_fail()
    test_cancel_fail()
    # this needs to be the hostname of a PDL server that does not require a
    # registered public key
    # internalhub = sys.argv[1]
    # _test_send(internalhub)
