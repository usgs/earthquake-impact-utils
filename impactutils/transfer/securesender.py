#!/usr/bin/env python

# stdlib imports
import os.path
import datetime
import getpass

# depends on https://github.com/jbardin/scp.py
# pip install git+git://github.com/jbardin/scp.py.git
from paramiko import SSHClient
from impactutils.extern.scp.scp import SCPClient
from .sender import Sender


class SecureSender(Sender):
    '''Class for sending files to a remote Unix-like system using ssh.

    SecureSender creates a remote directory if one does not already exist, and
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
      - remote_host String indicating the name of the remote host to which
        files should be copied.
      - remote_directory String indicating which directory input content
        should be copied to.
      - private_key Path to local RSA/DSA private key file which has been
        configured on the remote system.
    '''
    _required_properties = ['private_key', 'remote_host', 'remote_directory']
    _optional_properties = []

    def send(self):
        '''
        Send any files or folders that have been passed to constructor to a
        remote Unix-like system.

        Returns:
            Tuple of Number of files sent to remote SSH server and a message
            describing success.

        Raises:
            Exception when unable to create remote folder on remote host, or
            copy file to remote host.
        '''
        # figure out the remote folder
        remote_folder = self._properties['remote_directory']
        remote_host = self._properties['remote_host']
        # connect to remote system and instantiate scp object
        nfiles = 0
        ssh = self._connect()
        # SCPCLient takes a paramiko transport as its only argument
        scp = SCPClient(ssh.get_transport())

        # make sure the remote system has directory or it can be created.
        res = self._make_remote_folder(scp, ssh, remote_folder)
        if not res:
            msg = (f'Unable to create remote folder {remote_folder} '
                   f'on host {remote_host}')
            raise Exception(msg)

        # do the copying
        try:
            allfiles = []
            if len(self._local_files):
                allfiles = self._local_files
                for filename in allfiles:
                    self._copy_file_with_path(
                        scp, ssh, filename, remote_folder)

            if self._local_directory is not None:
                allfiles = self.getAllLocalFiles()
                for filename in allfiles:
                    self._copy_file_with_path(
                        scp, ssh, filename, remote_folder,
                        local_folder=self._local_directory)

        except Exception as obj:
            rhost = self._properties['remote_host']
            raise Exception(
                f'Could not send files to remote host {rhost}: "{str(obj)}"')

        nfiles += len(self._local_files)
        if self._local_directory is not None:
            nfiles += sum([len(files)
                           for r, d, files in os.walk(self._local_directory)])
        scp.close()
        ssh.close()
        msg = f'{int(nfiles):d} files sent to remote host {remote_host}'
        return (nfiles, msg)

    def cancel(self, cancel_content=None):
        """
        Create a cancel file (named as indicated in constructor "cancelfile"
        parameter) in remote_directory on remote_host.

        Args:
            cancel_content: String containing text that should be written to
                the cancelfile.

        Returns:
            A string message describing what has occurred.
        """
        remote_folder = self._properties['remote_directory']
        remote_host = self._properties['remote_host']
        ssh = self._connect()
        cancelfile = os.path.join(remote_folder, self._cancelfile)
        echo_cmd = f'echo {cancel_content} > {cancelfile}'
        stdin, stdout, stderr1 = ssh.exec_command(echo_cmd)
        chk_cmd = f'[ -e {cancelfile} ];echo $?'
        stdin, stdout, stderr = ssh.exec_command(chk_cmd)
        exists = not int(stdout.read().decode('utf-8').strip())
        if not exists:
            err = stderr1.read().decode('utf-8').strip()
            fmt = (f'Could not create {cancelfile} file on '
                   f'remote_host {remote_host} due to error: {err}')
            raise Exception(fmt)

        msg = ('A .cancel file has been placed in remote '
               f'directory {remote_folder}.')
        return (msg)

    def _connect(self):
        """Initiate an ssh connection with properties passed to constructor.

        Returns:
            Instance of the paramiko SSHClient class.

        Raises:
            Exception if connection to remote host fails.
        """
        ssh = SSHClient()
        # load hosts found in ~/.ssh/known_hosts
        # should we not assume that the user has these configured already?
        ssh.load_system_host_keys()
        remote_user = getpass.getuser()
        if 'remote_user' in self._properties:
            remote_user = self._properties['remote_user']
        try:
            ssh.connect(self._properties['remote_host'],
                        username=remote_user,
                        key_filename=self._properties['private_key'],
                        compress=True)
        except Exception as obj:
            msg = ("Could not connect with private key "
                   f"file {self._properties['private_key']}: "
                   f"Error '{str(obj)}")
            raise Exception(msg)
        return ssh

    def _copy_file_with_path(self, scp, ssh, local_file, remote_folder,
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
            scp: SCPClient instance.
            ssh: SSHClient instance.
            local_file: Local file to copy.
            remote_folder: Remote folder to copy local files to.
            local_folder: Top of local directory where file copying started.
                If None, local_file should be copied to a file of the same
                name (not preserving path) into remote_folder.
        """
        remote_host = self._properties['remote_host']
        if local_folder is not None:
            local_parts = local_file.replace(local_folder, '').strip(
                os.path.sep).split(os.path.sep)
            remote_parts = remote_folder.strip(os.path.sep).split(os.path.sep)
            all_parts = [os.path.sep] + remote_parts + local_parts
            remote_file = os.path.join(*all_parts)
            root, rfile = os.path.split(remote_file)
            exists, isdir = self._check_remote_folder(ssh, root)
            if not isdir:
                res = self._make_remote_folder(scp, ssh, root)
                if not res:
                    fmt = (f'Could not copy local file {local_file} '
                           f'to folder {remote_folder} '
                           f'on host {remote_host}')
                    raise Exception(fmt)

        else:
            root, tfile = os.path.split(local_file)
            remote_file = os.path.join(remote_folder, tfile)
        remote_tmp_file = remote_file + '.tmp_' + \
            datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
        print(f'Copying {local_file}...')
        scp.put(local_file, remote_tmp_file)
        rename_cmd = f'mv {remote_tmp_file} {remote_file}'
        stdin, stdout, stderr = ssh.exec_command(rename_cmd)

    def _check_remote_folder(self, ssh, remote_folder):
        """Check to see if remote folder exists and is a directory.

        Args:
            ssh: SSHClient instance.
            remote_folder: Remote folder to copy local files to.

        Returns:
            Tuple with two booleans -- (does a file or directory of this name
            exist, is it a directory?)
        """
        chk_cmd1 = f'[ -e {remote_folder} ];echo $?'
        stdin, stdout, stderr = ssh.exec_command(chk_cmd1)
        exists = not int(stdout.read().decode('utf-8').strip())
        chk_cmd2 = f'[ -d {remote_folder} ];echo $?'
        stdin, stdout, stderr = ssh.exec_command(chk_cmd2)
        isdir = not int(stdout.read().decode('utf-8').strip())
        return (exists, isdir)

    def _make_remote_folder(self, scp, ssh, remote_folder):
        """Make a folder on remote system.

        Args:
            scp: SCPClient instance.
            ssh: SSHClient instance.
            remote_folder: Remote folder to copy local files to.

        Returns:
            Boolean indicating success or failure.
        """
        exists, isdir = self._check_remote_folder(ssh, remote_folder)
        chk_cmd1 = f'[ -d {remote_folder} ];echo $?'
        if not isdir:
            if exists:
                rm_cmd = f'rm {remote_folder}'
                stdin, stdout, stderr = ssh.exec_command(rm_cmd)
                stdin, stdout, stderr = ssh.exec_command(chk_cmd1)
                exists = not int(stdout.read().decode('utf-8').strip())
            if not exists:
                mk_cmd = f'mkdir -p {remote_folder}'
                stdin, stdout, stderr = ssh.exec_command(mk_cmd)
                exists, isdir = self._check_remote_folder(ssh, remote_folder)
                if not isdir:
                    return False
        return True
