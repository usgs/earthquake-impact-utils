#!/usr/bin/env python

# stdlib imports
import shutil
import os.path
import datetime

# local imports
from .sender import Sender


class CopySender(Sender):
    '''
    Class for sending and deleting files and directories via system copy
    and delete.

    CopySender creates a remote directory if one does not already exist, and
    copies files and directories to that remote directory.  Files are simply
    copied to the remote_directory.  Files in the local directory are copied
    to the remote directory, and sub-directories under the local directory are
    preserved in the remote directory.

    For example:
      If the local_directory is /home/user/event1/, which contains:
      /home/user/event1/datafile1.txt
      /home/user/event1/other/datafile2.txt

      and the remote_directory is /data/event1, then it will contain:
      /data/event1/datafile1.txt
      /data/event1/other/datafile2.txt

    The cancel() method implemented in this class behaves as follows:
    cs = CopySender(properties={'remote_directory':'/data/event1'},
                    local_directory='/home/user/event1',cancelfile='CANCEL')
    #Sending...
    cs.cancel() #=>This creates a file called /data/event1/CANCEL.

    Required properties:
      - remote_directory String indicating which directory input content
        should be copied to.

    '''
    _required_properties = ['remote_directory']
    _optional_properties = []

    def send(self):
        '''Send any files or folders that have been passed to constructor.

        This method deletes any previous cancel files that may exist in the
        remote_directory.

        Returns:
            Tuple containing number of files sent to local directory, and a
            message describing success.

        '''
        # copy directories to remote location, changing remote name to desired
        # alias
        remote_folder = self._properties['remote_directory']

        # remove any previous cancel files sent to remote_folder
        cancelfile = os.path.join(remote_folder, self._cancelfile)
        if os.path.isfile(cancelfile):
            os.remove(cancelfile)

        nfiles = 0
        if not os.path.isdir(remote_folder):
            os.makedirs(remote_folder)
        if self._local_directory:
            local_folder = self._local_directory
            # recursively find all of the files locally, then
            # copy them to corresponding remote folder structure
            allfiles = self.getAllLocalFiles()
            for filename in allfiles:
                self._copy_file_with_path(
                    filename, remote_folder, local_folder=local_folder)
                nfiles += 1

            nfiles += sum([len(files)
                           for r, d, files in os.walk(local_folder)])

        # copy files to remote location
        for filename in self._local_files:
            self._copy_file_with_path(filename, remote_folder)
            nfiles += 1

        return (nfiles,
                f'{int(nfiles):d} files sent successfully using CopySender.')

    def cancel(self, cancel_content=None):
        """
        Create a cancel file (named as indicated in constructor "cancelfile"
        parameter) in remote_directory.

        Args:
            cancel_content: String containing text that should be written to
                the cancelfile.

        Returns:
            A string message describing what has occurred.
        """
        remote_folder = self._properties['remote_directory']
        cancelfile = os.path.join(remote_folder, self._cancelfile)
        f = open(cancelfile, 'wt')
        if cancel_content is not None:
            f.write(cancel_content)
        f.close()
        return (f'A .cancel file has been placed in remote directory {remote_folder}.')

    def _copy_file_with_path(self, local_file, remote_folder,
                             local_folder=None):
        """
        Copy local_file to remote_folder, preserving relative path and creating
        required sub-directories.

        Usage:
         local_file: /home/user/data/events/us2016abcd/data_files/datafile.txt
         remote_folder: /data/archive/events
         local_folder: /home/user/data/events/us2016abcd

         would create:
           /data/archive/events/us2016abcd/data_files/datafile.txt

        local_file: /home/user/data/events/us2016abcd/data_files/datafile.txt
        remote_folder: /data/archive/events/us2016abcd
        local_folder: None

        would create:
          /data/archive/events/us2016abcd/datafile.txt

        Args:
            local_file: Local file to copy.
            remote_folder: Remote folder to copy local files to.
            local_folder: Top of local directory where file copying started.
                If None, local_file should be copied to a file of the same
                name (not preserving path) into remote_folder.
        """
        if local_folder is not None:
            local_parts = local_file.replace(local_folder, '').strip(
                os.path.sep).split(os.path.sep)
            remote_parts = remote_folder.strip(os.path.sep).split(os.path.sep)
            all_parts = [os.path.sep] + remote_parts + local_parts
            remote_file = os.path.join(*all_parts)
            root, rfile = os.path.split(remote_file)
            if not os.path.isdir(root):
                os.makedirs(root)
        else:
            root, tfile = os.path.split(local_file)
            remote_file = os.path.join(remote_folder, tfile)
        remote_tmp_file = remote_file + '.tmp_' + \
            datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
        shutil.copyfile(local_file, remote_tmp_file)
        os.rename(remote_tmp_file, remote_file)
