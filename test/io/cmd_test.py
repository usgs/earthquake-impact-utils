#!/usr/bin/env python

#stdlib imports
import os.path
import sys

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
impactdir = os.path.abspath(os.path.join(homedir,'..','..'))
sys.path.insert(0,impactdir) #put this at the front of the system path, ignoring any installed impact stuff

from impactutils.io.cmd import get_command_output

def test_get_command_output():
    cmd = 'ls *.py'
    rc, so, se = get_command_output(cmd)
    assert rc == True

    cmd = 'ls asdf'
    rc, so, se = get_command_output(cmd)
    assert rc == False

if __name__ == '__main__':
    test_get_command_output()
