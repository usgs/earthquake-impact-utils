#!/usr/bin/env python

# stdlib imports
import sys
import os.path
from unittest import mock, TestCase

# third party imports
import pytest

# local imports
from impactutils.transfer.securesender import SecureSender

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
# put this at the front of the system path, ignoring any installed mapio stuff
sys.path.insert(0, shakedir)


def _testKey(remotehost, remotefolder, privatekey):
    props = {'remote_host': remotehost,
             'remote_directory': remotefolder,
             'private_key': privatekey}
    thisfile = os.path.abspath(__file__)
    securesend = SecureSender(properties=props, local_files=[thisfile])
    securesend.send()

    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    securesend = SecureSender(properties=props, local_directory=homedir)
    securesend.send()
    securesend.cancel(cancel_content='This is a cancel message')


class MockSTDIO(TestCase):
    def read(self):
        return bytes("0".encode('utf-8'))


class MockSSH(TestCase):
    def connect(self):
        pass

    def load_system_host_keys(self):
        pass

    def get_transport(self):
        pass

    def exec_command(self, cmd):
        return (MockSTDIO(), MockSTDIO(), MockSTDIO())

    def close(self):
        return


class MockSCP(TestCase):  # This class inherits unittest.TestCase
    def put(self, local, remote):
        return

    def close(self):
        return


def test_mock_send():
    props = {'remote_host': '',
             'remote_directory': '',
             'private_key': ''}
    thisfile = os.path.abspath(__file__)
    homedir = os.path.dirname(os.path.abspath(
        __file__))
    connect = 'impactutils.transfer.securesender.SecureSender._connect'
    client = 'impactutils.transfer.securesender.SCPClient'

    # file
    with mock.patch(connect) as mock_connect, \
            mock.patch(client) as mock_client:
        # error code, stdout, stderr
        mock_connect.return_value = MockSSH()
        mock_client.return_value = MockSCP()
        securesend = SecureSender(properties=props, local_files=[thisfile])
        securesend.send()

    # directory
    with mock.patch(connect) as mock_connect, \
            mock.patch(client) as mock_client:
        # error code, stdout, stderr
        mock_connect.return_value = MockSSH()
        mock_client.return_value = MockSCP()
        securesend = SecureSender(properties=props, local_directory=homedir)
        securesend.send()


def test_mock_cancel():
    props = {'remote_host': '',
             'remote_directory': '',
             'private_key': ''}
    thisfile = os.path.abspath(__file__)
    connect = 'impactutils.transfer.securesender.SecureSender._connect'
    client = 'impactutils.transfer.securesender.SCPClient'

    # file
    with mock.patch(connect) as mock_connect, \
            mock.patch(client) as mock_client:
        # error code, stdout, stderr
        mock_connect.return_value = MockSSH()
        mock_client.return_value = MockSCP()
        securesend = SecureSender(properties=props, local_files=[thisfile])
        securesend.cancel()

    # directory
    with mock.patch(connect) as mock_connect, \
            mock.patch(client) as mock_client:
        # error code, stdout, stderr
        mock_connect.return_value = MockSSH()
        mock_client.return_value = MockSCP()
        securesend = SecureSender(properties=props, local_directory=homedir)
        securesend.cancel()


def test_exceptions():
    props = {'remote_host': '',
             'remote_directory': '',
             'private_key': ''}
    thisfile = os.path.abspath(__file__)
    match_msg = "not connect with private key file"
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    with pytest.raises(Exception, match=match_msg) as a:
        securesend = SecureSender(properties=props, local_files=[thisfile])
        securesend.send()

    with pytest.raises(Exception, match=match_msg) as a:
        securesend = SecureSender(properties=props, local_directory=homedir)
        securesend.send()

    with pytest.raises(Exception, match=match_msg) as a:
        securesend = SecureSender(properties=props, local_directory=homedir)
        securesend.cancel(cancel_content='This is a cancel message')


if __name__ == '__main__':
    test_mock_send()
    test_mock_cancel()
    test_exceptions()
    if len(sys.argv) > 1:
        remotehost = sys.argv[1]
        remotefolder = sys.argv[2]
        privatekey = sys.argv[3]
        _testKey(remotehost, remotefolder, privatekey)
