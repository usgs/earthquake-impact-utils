#!/usr/bin/env python

# stdlib imports
import os.path
import sys
from unittest import mock, TestCase
import urllib.request
import urllib.error
import urllib.parse

# local imports
from impactutils.transfer.ftpsender import FTPSender

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
# put this at the front of the system path, ignoring any installed mapio stuff
sys.path.insert(0, shakedir)


class MockFTP(TestCase):
    def __init__(self, folder):
        pass

    def close(self):
        pass

    def connect(self):
        pass

    def cwd(self, folder):
        pass

    def exec_command(self, cmd):
        return (MockSTDIO(), MockSTDIO(), MockSTDIO())

    def get_transport(self):
        pass

    def load_system_host_keys(self):
        pass

    def quit(self):
        pass

    def rename(self, tmp, path):
        pass

    def storbinary(self, cmd, file, num):
        pass


def test_mock_send_file():
    properties = {'remote_host': 'host',
                  'remote_directory': 'folder',
                  'user': 'user',
                  'password': 'password'}
    print('Testing sending single file...')
    thisfile = os.path.abspath(__file__)
    thispath, thisfilename = os.path.split(thisfile)
    cancelfile = 'CANCEL'

    ftp = 'impactutils.transfer.ftpsender.FTPSender._setup'
    # file
    with mock.patch(ftp) as mock_ftp:
        mock_ftp.return_value = MockFTP('folder')
        sender = FTPSender(properties=properties, local_files=[
                           thisfile], cancelfile=cancelfile)
        nfiles, send_msg = sender.send()
        assert nfiles == 1
        assert 'successfully' in send_msg
        sender.cancel()

    print('Testing sending folder...')
    thisroot, thisbase = os.path.split(thispath)
    cancelfile = 'CANCEL'
    with mock.patch(ftp) as mock_ftp:
        sender = FTPSender(properties=properties,
                           local_directory=thispath, cancelfile=cancelfile)
        nfiles, send_msg = sender.send()
        assert 'sent successfully' in send_msg
        cancel_msg = sender.cancel()
        sender._create_remote_directory(MockFTP(''), '')

def _test_send_file(properties):
    print('Testing sending single file...')
    thisfile = os.path.abspath(__file__)
    thispath, thisfilename = os.path.split(thisfile)
    cancelfile = 'CANCEL'
    try:
        sender = FTPSender(properties=properties, local_files=[
                           thisfile], cancelfile=cancelfile)
        nfiles, send_msg = sender.send()
        url = f"ftp://{properties['remote_host']}{properties['remote_directory']}/{thisfilename}"
        fh = urllib.request.urlopen(url)
        fh.close()
        print(f'Successfully sent local file {thisfile}')
        cancel_msg = sender.cancel()
        url = f"ftp://{properties['remote_host']}{properties['remote_directory']}/{cancelfile}"
        fh = urllib.request.urlopen(url)
        fh.close()
        print(f'Successfully sent cancel message {thispath}')

    except Exception as obj:
        fmt = f"Test failed - you may have a file called {thisfile} on host {properties['remote_host']} and directory {properties['remote_directory']}"
        raise Exception(fmt)
    print('Passed sending single file.')


def _test_send_folder(properties):
    # modify this to create a temporary folder and send that - I think __pycache__ is screwing up the deletes...
    # although maybe I should test deleting directories with directories in
    # them...
    print('Testing sending folder...')
    thisfile = os.path.abspath(__file__)
    thispath, thisfilename = os.path.split(thisfile)
    thisroot, thisbase = os.path.split(thispath)
    cancelfile = 'CANCEL'
    try:
        sender = FTPSender(properties=properties,
                           local_directory=thispath, cancelfile=cancelfile)
        nfiles, send_msg = sender.send()
        url = f"ftp://{properties['remote_host']}{properties['remote_directory']}"

        # this should succeed
        fh = urllib.request.urlopen(url)
        fh.close()
        print(f'Successfully sent local folder {thispath}')
        cancel_msg = sender.cancel()
        url = f"ftp://{properties['remote_host']}{properties['remote_directory']}/{cancelfile}"
        fh = urllib.request.urlopen(url)
        fh.close()
        print(f'Successfully sent cancel message {thispath}')

    except Exception as obj:
        fmt = f"Test failed - you may have a file called {thisfile} on host {properties['remote_host']} and directory {['remote_directory']}"
        raise Exception(fmt)
    print('Passed sending folder.')


def test_exceptions():
    thisfile = os.path.abspath(__file__)
    thispath, thisfilename = os.path.split(thisfile)
    thisroot, thisbase = os.path.split(thispath)
    cancelfile = 'CANCEL'
    user = ''
    password = 'user@anonymous.org'
    properties = {'remote_host': '',
                  'remote_directory': '.',
                  'user': user,
                  'password': password}
    sender = FTPSender(properties=properties, local_files=[
        thisfile], cancelfile=cancelfile)

    # The error should have to do with a nonexistent ftp
    fail = False
    try:
        sender.send()
    except Exception as e:
        assert "'NoneType' object has no attribute 'sendall'" in str(e)
        fail = True
    assert fail == True

    fail = False
    try:
        sender.cancel()
    except Exception as e:
        assert "'NoneType' object has no attribute 'sendall'" in str(e)
        fail = True
    assert fail == True


if __name__ == '__main__':
    test_mock_send_file()
    test_exceptions()
    if len(sys.argv) > 1:
        # try logging into an FTP server that supports anonymous login
        host = sys.argv[1]
        folder = sys.argv[2]
        user = ''
        password = 'user@anonymous.org'
        props = {'remote_host': host,
                 'remote_directory': folder,
                 'user': user,
                 'password': password}
        _test_send_file(props)
        _test_send_folder(props)
