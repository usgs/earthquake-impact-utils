#!/usr/bin/env python

# stdlib imports
import os.path


class Sender(object):
    '''Base class for concrete subclasses that wrap around different methods of transmitting/deleting files.

    Each subclass should provide class variables called:
    _required_properties: A list of names of *required* properties that MUST be passed in to constructor.
    _optional_properties: A list of names of *optional* properties that CAN be passed in to constructor.

    Each subclass should implement at least three methods:
    send() => do the appropriate implementation of transferring files
    delete() => do the appropriate implementation of deleting transferred files from remote system, if possible.
    cancel() => do the appropriate implementation of sending a cancel message to remote system, if possible.

    delete() and cancel() may do the same thing, or nothing.
    '''
    _required_properties = []
    _optional_properties = []
    def __init__(self, properties=None, local_files=None, local_directory=None, cancelfile='.cancel'):
        """Create a Sender object using property settings, local files and directories to transfer/delete.

        :param properties:
          Dictionary of properties that are needed for a specific subclass of sender.
        :param local_files:
          List of local files which should be transferred to remote system.
        :param local_directory:
          Local directory which should be transferred to remote system.
        :param cancelfile:
          For Sender subclasses that actually send a file for cancel() actions, 
          this allows the user to define what that file is called.
        """
        self._properties = properties
        for prop in self._required_properties:
            if prop not in self._properties:
                raise Exception('Required property "%s" not specified.' % prop)
            
        if local_files is not None:
            if not isinstance(local_files, list):
                raise Exception('Input files must be a list')
            for f in local_files:
                if not os.path.isfile(f):
                    raise Exception(
                        'Input file %s could not be found' % f)

        if local_directory is not None:
            if not os.path.isdir(local_directory):
                raise Exception(
                    'Input directory %s could not be found' % directory)
        if local_files is not None:
            self._local_files = local_files
        else:
            self._local_files = []
            
        self._local_directory = None
        if local_directory is not None:
            self._local_directory = local_directory

        #set the name of the cancel file
        self._cancelfile = cancelfile

    def addProperty(self, key, value):
        self._properties[key] = value

    def getRequiredProperties(self):
        return self._required_properties

    def getOptionalProperties(self):
        return self._optional_properties
    
    def addFiles(self, local_files):
        for f in files:
            if not os.path.isfile(f):
                raise Exception('Input file %s could not be found' % f)
        self._local_files += local_files

    def changeDirectory(self, local_directory,directory_alias=None):
        if not os.path.isdir(local_directory):
            raise Exception(
                'Input directory %s could not be found' % directory)
        self._local_directory = local_directory
        self._directory_alias = directory_alias

    def getAllLocalFiles(self):
        """Recursively find all files in local directory, create a list of each file with full path.
        
        :returns:
          List of files with full path underneath input local_directory.
        """
        allfiles = []
        if not self._local_directory:
            return allfiles
        for root, dirs, files in os.walk(self._local_directory):
            for fname in files:
                filename = os.path.join(root,fname)
                allfiles.append(filename)
        return allfiles

    # this is implemented in the subclasses
    def send(self):
        """

        :returns:
          Tuple containing number of files sent, and a message describing what was done.
        """
        pass

    #this is implemented in the subclasses
    def cancel(self):
        """

        :returns:
          A message describing what was done.
        """
        pass

    def getRequiredProperties(self):
        """Return the list of names of required properties for given subclass.

        :returns:
          List of names of required properties for given subclass.
        """
        return self._required_properties

    def getOptionalProperties(self):
        """Return the list of names of optional properties for given subclass.

        :returns:
          List of names of optional properties for given subclass.
        """
        return self._optional_properties

    
        
