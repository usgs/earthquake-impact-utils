#!/usr/bin/env python

# stdlib imports
import shutil
import os.path

# local imports
from .sender import Sender

class CopySender(Sender):
    '''(Really simple) Class for sending and deleting files and directories via system copy and delete.
    '''

    def send(self):
        '''
        Send any files or folders that have been passed to constructor.

        Returns:
            Number of files sent to local directory.
        '''
        nfiles = 0
        if 'directory' not in self.properties:
            raise Exception('Property "directory" not specified.')

        for folder in self.directories:
            if not os.path.isdir(folder):
                raise Exception('Input directory %s does not exist.' % folder)

        for filename in self.files:
            shutil.copy(filename, self.properties['directory'])

        nfiles += len(self.files)

        for folder in self.directories:
            shutil.copytree(folder, self.properties['directory'])
            nfiles += sum([len(files) for r, d, files in os.walk(folder)])

        return nfiles

    def delete(self):
        '''
        Delete any files and folders that have been passed to constructor.

        Returns:
            The number of files deleted from local directory.
        '''
        if 'directory' not in self.properties:
            raise Exception('Property "directory" not specified.')

        if not os.path.isdir(self.properties['directory']):
            raise Exception(
                'Output directory "%s" does not exist.' % self.properties['directory'])

        for filename in self.files:
            fname = os.path.split(filename)[1]
            dfile = os.path.join(self.properties['directory'], fname)
            os.remove(dfile)

        for folder in self.directories:
            dirname = os.path.split(folder)[1]
            dfolder = os.path.join(self.properties['directory'], dirname)
            shutil.rmtree(dfolder)
