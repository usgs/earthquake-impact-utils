#!/usr/bin/env python

# stdlib imports
import os.path
import sys
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


if __name__ == '__main__':
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
