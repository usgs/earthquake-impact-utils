#!/usr/bin/env python

# stdlib imports
import sys
import os.path

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
# put this at the front of the system path, ignoring any installed mapio stuff
sys.path.insert(0, shakedir)

from impactutils.transfer.securesender import SecureSender


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


if __name__ == '__main__':
    remotehost = sys.argv[1]
    remotefolder = sys.argv[2]
    privatekey = sys.argv[3]
    _testKey(remotehost, remotefolder, privatekey)
