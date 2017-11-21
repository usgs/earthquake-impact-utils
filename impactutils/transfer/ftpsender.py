#!/usr/bin/env python

# stdlib imports
from ftplib import FTP, error_perm
import os.path
import shutil
import tempfile

# local
from .sender import Sender


class FTPSender(Sender):
    '''Class for sending and deleting files and directories via FTP.

    PDLSender uses a local installation of Product Distribution Layer (PDL)
    (https://ehppdl1.cr.usgs.gov/index.html#documentation)
    to send a file or a directory, along with desired metadata to one or more
    PDL hubs.

    Required properties:
      - remote_host Name of FTP server.
      - remote_directory String path on remote_host where local files should
        be copied to.

    Optional properties:
      - user String user name, for FTP servers where anonymous login is not
        allowed.
      - password String password, for FTP servers where anonymous login is
        not allowed.

    Usage:
    sender = FTPSender(properties={'remote_host':'ftp.gov',
                                   'remote_directory':'/pub/incoming/event1'},
                       local_directory = '/home/user/event1')
    sender.send() => Creates remote url: ftp://ftp.gov/pub/incoming/event1 with contents of /home/user/event1 in it.

    OR

    sender = FTPSender(properties={'remote_host':'ftp.gov',
                                   'remote_directory':'/pub/incoming/event1'},
                       local_directory = '/home/user/event1/version1')
    sender.send() => Creates remote url: ftp://ftp.gov/pub/incoming/event1 with contents of /home/user/event1/version1 in it.

    OR
    sender = FTPSender(properties={'remote_host':'ftp.gov',
                                   'remote_directory':'/pub/incoming/event1'},
                       local_files = ['/home/user/event1/version1/file1.txt','/home/user/event1/version1/file2.txt'])
    sender.send() => Creates remote files: ftp://ftp.gov/pub/incoming/event1/file1.txt AND
                                           ftp://ftp.gov/pub/incoming/event1/file1.txt

    '''
    _required_properties = ['remote_directory', 'remote_host']
    _optional_properties = ['user', 'password']

    def send(self):
        '''
        Send any files or folders that have been passed to constructor.

        Returns:
            Tuple of Number of files sent to remote SSH server and message
            describing success.

        Raises:
            Exception when files cannot be sent to remote FTP server for any
            reason.
        '''
        remote_host = self._properties['remote_host']
        remote_folder = self._properties['remote_directory']

        try:
            # this should put us at the top level folder
            ftp = self._setup()

            # send any files we want
            nfiles = 0
            for f in self._local_files:
                self.__sendfile(f, ftp)
                nfiles += 1

            # send everything in the directories we specified
            if self._local_directory is not None:
                local_directory = self._local_directory
                allfiles = self.getAllLocalFiles()
                for filename in allfiles:
                    try:
                        self._copy_file_with_path(
                            ftp, filename, remote_folder,
                            local_folder=local_directory)
                        nfiles += 1
                    except:
                        x = 1

            ftp.quit()
            return (nfiles, '%i files were sent successfully to %s %s'
                    % (nfiles, remote_host, remote_folder))
        except Exception as obj:
            raise Exception(
                'Could not send to %s.  Error "%s"' % (host, str(obj)))

    def cancel(self):
        """
        Create a cancel file (named as indicated in constructor "cancelfile"
        parameter) in remote_directory on remote_host.

        Args:
            cancel_content: String containing text that should be written to
                the cancelfile.

        Returns:
            A string message describing what has occurred.
        """
        remote_host = self._properties['remote_host']
        remote_folder = self._properties['remote_directory']
        ftp = self._setup()

        # Create local .cancel file, then copy it to ftp server
        tempdir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(tempdir, self._cancelfile)  # local file
            f = open(tfile, 'wt')
            f.close()
            ftp.cwd(remote_folder)
            self.__sendfile(tfile, ftp)
        except Exception as e:
            raise Exception('Could not create .cancel file on %s/%s' %
                            (remote_host, remote_folder))
        finally:
            shutil.rmtree(tempdir)
        return ('%s file succesfully placed on %s %s'
                % (self._cancelfile, remote_host, remote_folder))

    def _setup(self):
        """Initiate an ftp connection with properties passed to constructor.

        Navigate to/create directory (as necessary) specified by
        remote_directory property.

        Returns:
            Instance of the ftplib.FTP class.
        """
        host = self._properties['remote_host']
        remote_folder = self._properties['remote_directory']
        # attempt to login to remote host
        try:
            dirparts = self._split(remote_folder)
            ftp = FTP(host)
            if 'user' in self._properties:
                user = self._properties['user']
            else:
                user = ''
            if 'password' in self._properties:
                password = self._properties['password']
            else:
                password = ''
            if user == '':
                ftp.login()
            else:
                ftp.login(user, password)
        except error_perm as msg:
            raise Exception('Could not login to remote host %s' % (host))

        # attempt to cd to remote directory
        try:
            self._create_remote_directory(ftp, remote_folder)
        except Exception as e:
            ftp.quit()
            raise Exception(
                    'Could not navigate to directory "%s" on remote host %s'
                    % (remote_folder, host))

        return ftp

    def _create_remote_directory(self, ftp, remote_directory):
        """Create directory (recursively) on remote_host.

        Args:
            ftp: ftplib.FTP instance.
            remote_directory: String path of directory on remote system which
                needs to be created.

        Raises:
            Exception when unable to create remote_directory.
        """
        # attempt to cd to remote directory
        ftp.cwd('/')
        try:
            ftp.cwd(remote_directory)
        except error_perm as msg:
            dirparts = self._split(remote_directory)
            for directory in dirparts:
                try:
                    ftp.cwd(directory)
                except error_perm as msg:
                    try:
                        ftp.mkd(directory)
                        ftp.cwd(directory)
                    except error_perm as msg:
                        raise Exception(
                            'Unable to create subdirectory %s.' % (directory))

    def _copy_file_with_path(self, ftp, local_file, remote_folder,
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
        if local_folder is None:
            ftp.cwd(remote_folder)
            self.__sendfile(filename, ftp)
        else:
            local_parts = local_file.replace(local_folder, '').strip(
                os.path.sep).split(os.path.sep)
            remote_parts = self._split(remote_folder)
            all_parts = remote_parts + local_parts
            remote_file = '/' + '/'.join(all_parts)
            print(remote_file)
            remfolder, remfile = self._path_split(remote_file)
            try:
                ftp.cwd(remfolder)
            except error_perm as ep:
                self._create_remote_directory(ftp, remfolder)

            self.__sendfile(local_file, ftp)
            ftp.cwd(remote_folder)

    def __sendfile(self, filename, ftp):
        '''Internal function used to send a file using an FTP object.

        Args:
            filename: Local filename
            ftp: Instance of FTP object.
        '''
        # in case somebody is polling for this file,
        # make a temporary file first, then rename it
        # so the poller doesn't grab it before its finished transferring.
        fbase, fpath = os.path.split(filename)  # this is a local file
        tmpfile = fpath + '.tmp'
        cmd = "STOR " + tmpfile
        # we don't tell the ftp server about the local path to the file

        # actually send the file
        ftp.storbinary(cmd, open(filename, "rb"), 1024)
        # rename it to the desired destination
        ftp.rename(tmpfile, fpath)

    def _join(self, *path_parts):
        return '/' + '/'.join(path_parts)

    def _split(self, path):
        return path.strip('/').split('/')

    def _path_split(self, path):
        parts = path.strip('/').split('/')
        fname = parts[-1]
        fpath = '/' + '/'.join(parts[0:-1])
        return (fpath, fname)
