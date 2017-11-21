#!/usr/bin/env python

# stdlib imports
import os.path
import sys
import tempfile
import shutil

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
# put this at the front of the system path, ignoring any installed mapio stuff
sys.path.insert(0, shakedir)

from impactutils.transfer.factory import get_sender_class


def test():
    print('Testing basic file system copy...')
    thisfile = os.path.abspath(__file__)
    tempdir = tempfile.mkdtemp()
    try:
        sender_class = get_sender_class('copy')
        cpsender = sender_class(
            properties={'remote_directory': tempdir}, local_files=[thisfile])
        nfiles = cpsender.send()
        nfiles = cpsender.cancel()
    except Exception as obj:
        raise SenderError('Failed to copy or delete a file.')
    shutil.rmtree(tempdir)
    print('Passed basic file system copy.')


if __name__ == '__main__':
    test()
