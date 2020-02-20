#!/usr/bin/env python

# stdlib imports
import os.path
import datetime

# third party

# local
from .sender import Sender

# local imports
from impactutils.io.cmd import get_command_output
from impactutils.exceptions import PDLError

DATE_TIME_FMT = '%Y-%m-%dT%H:%M:%S.%f'


class PDLSender(Sender):
    """Class to invoke a PDL send command on a product.

    PDLSender uses a local installation of Product Distribution Layer (PDL)
    (https://ehppdl1.cr.usgs.gov/index.html#documentation)
    to send a file or a directory, along with desired metadata to one or more
    PDL hubs.

    Required properties:
      - java String path to Java executable on this system.
      - jarfile String path to PDL .jar file on this system.
      - privatekey String path to PDL private key file.
      - configfile String path to PDL config file (specifying remote hubs,
        ports, etc.)
      - source Source of this product (i.e., contributor of the product).
        i.e. 'us'
      - type  Product type (i.e. shakemap, losspager, etc.)
      - eventsource Source of the original event ID. i.e., ci, gcmt, etc.
      - eventsourcecode Event ID (as issued by source - i.e., 2008abcd)
      - code  eventsource + eventsourcecode

    Optional properties:
      - latitude Float latitude of event.
      - longitude Float longitude of event.
      - depth Float depth of event.
      - magnitude Float magnitude of event.
      - eventtime datetime.datetime object indicating time of origin.

    Product properties:
      Any string, int, float, or datetime.datetime object which the user would
      like to pass to PDL.
    """

    _pdlcmd_pieces = ['[JAVA] -jar [JARFILE] --send --status=[STATUS]',
                      '--source=[SOURCE] --type=[TYPE] --code=[CODE]',
                      '--eventsource=[EVENTSOURCE] --eventsourcecode=[EVENTSOURCECODE]',
                      '[PRODUCT_PROPERTIES] [OPTIONAL_PROPERTIES]',
                      '--privateKey=[PRIVATEKEY]  --configFile=[CONFIGFILE] [FILE] [DIRECTORY]']
    _pdlcmd = ' '.join(_pdlcmd_pieces)

    _required_properties = ['java', 'jarfile', 'privatekey', 'configfile',
                            'source', 'type', 'code',
                            'eventsource', 'eventsourcecode']
    _optional_properties = ['latitude', 'longitude',
                            'depth', 'magnitude', 'eventtime']
    _optional_properties_fmt = {'latitude': '%.4f',
                                'longitude': '%.4f',
                                'depth': '%.1f',
                                'magnitude': '%.1f',
                                'eventtime': DATE_TIME_FMT}

    def __init__(self, properties=None, local_files=None, local_directory=None,
                 cancelfile='.cancel', product_properties=None):
        """
        Create a PDLSender object using property settings, local files and
        directories to transfer/delete.

        Args:
            properties: Dictionary of properties that are needed for a PDL.
            local_files: List of local files which should be transferred to
                remote system.
            local_directory: Local directory which should be transferred to
                remote system.
            cancelfile: For Sender subclasses that actually send a file for
                cancel() actions, this allows the user to define what that
                file is called.
            product_properties: A dictionary of arbitrary properties that will
                be passed to PDL as --property-PROPERTY_NAME=PROPERTY_VALUE.
                These properties can be ints, floats, strings, or datetime
                objects.  Other kinds of objects will be converted to strings
                using the str() method - unpredictable results may follow.

        """
        if product_properties is not None:
            self._product_properties = product_properties.copy()

        super().__init__(properties=properties, local_files=local_files,
                         local_directory=local_directory, cancelfile=cancelfile)

    def _replace_required_properties(self, cmd):
        for propkey in self._required_properties:
            propvalue = self._properties[propkey]
            cmd = cmd.replace('[' + propkey.upper() + ']', propvalue)
        return cmd

    def _replace_product_properties(self, cmd):
        if hasattr(self, '_product_properties'):
            prop_nuggets = []
            for propkey, propvalue in self._product_properties.items():
                if isinstance(propvalue, float):
                    prop_nuggets.append(
                        f'--property-{propkey}={propvalue:.4f}')
                elif isinstance(propvalue, int):
                    prop_nuggets.append(
                        f'--property-{propkey}={int(propvalue):d}')
                elif isinstance(propvalue, datetime.datetime):
                    prop_nuggets.append(
                        f'--property-{propkey}={propvalue.strftime(DATE_TIME_FMT)[0:23]}')
                elif isinstance(propvalue, str):
                    prop_nuggets.append(f'--property-{propkey}="{propvalue}"')
                else:
                    prop_nuggets.append(
                        f'--property-{propkey}={str(propvalue)}')
            cmd = cmd.replace('[PRODUCT_PROPERTIES]', ' '.join(prop_nuggets))
        else:
            cmd = cmd.replace('[PRODUCT_PROPERTIES]', '')
        return cmd

    def _replace_files(self, cmd):
        if self._local_files:
            cmd = cmd.replace('[FILE]', f'--file={self._local_files[0]}')
        else:
            cmd = cmd.replace('[FILE]', '')
        if self._local_directory:
            cmd = cmd.replace(
                '[DIRECTORY]', f'--directory={self._local_directory}')
        else:
            cmd = cmd.replace('[DIRECTORY]', '')

        return cmd

    def _replace_optional_properties(self, cmd):
        # add optional properties
        opts = set(self._optional_properties)
        props = set(self._properties.keys())
        hasopts = len(opts & props)

        if hasopts:
            opt_nuggets = []
            for propkey in self._optional_properties:
                if propkey in self._properties:
                    if propkey == 'eventtime':
                        opt_nuggets.append(
                            f'--{propkey}={self._properties[propkey].strftime(DATE_TIME_FMT)[0:23]}Z')
                    else:
                        fmt = '--%s=' + self._optional_properties_fmt[propkey]
                        opt_nuggets.append(
                            fmt % (propkey, self._properties[propkey]))
            cmd = cmd.replace('[OPTIONAL_PROPERTIES]', ' '.join(opt_nuggets))
        else:
            cmd = cmd.replace('[OPTIONAL_PROPERTIES]', '')

        return cmd

    def send(self):
        """Send local file or directory via PDL.

        Raises:
            Exception when:
             - number of local_files is greater than 1.
             - PDL command fails for any reason.

        Returns:
            Tuple containing number of files sent, and the standard output of
            the PDL command.
        """
        # we can really only support sending of one file, so error out
        # if someone has specified more than one.
        if len(self._local_files) > 1:
            raise PDLError('For PDL, you may only send one file at a time.')

        # build pdl command line from properties
        cmd = self._pdlcmd

        # make this an update status
        cmd = cmd.replace('[STATUS]', 'UPDATE')

        # fill out the required properties
        cmd = self._replace_required_properties(cmd)

        # fill out any files or directories we'll be sending
        cmd = self._replace_files(cmd)

        # fill in all the product properties
        cmd = self._replace_product_properties(cmd)

        # fill in all the optional properties
        cmd = self._replace_optional_properties(cmd)

        # call PDL on the command line
        retcode, stdout, stderr = get_command_output(cmd)
        if not retcode:
            ptype = self._properties['type']
            fmt = f'Could not send product "{ptype}" due to error "{stdout + stderr}"'
            raise PDLError(fmt)

        # return the number of files we just sent
        nfiles = 0
        if self._local_files:
            nfiles += 1
        if self._local_directory:
            nfiles += sum([len(files)
                           for r, d, files in os.walk(self._local_directory)])
        numfiles = int(nfiles)
        error_msg = stdout.decode('utf-8')
        msg = f'{numfiles:d} files sent successfully: resulting in output: "{error_msg}"'
        return (nfiles, msg)

    def cancel(self, cancel_content=None):
        """Send a delete message out via PDL regarding the product in question.

        Args:
            cancel_content: String containing cancel message. This is NOT used
                in the implementation for this class.

        Returns:
            Standard output from PDL DELETE command.
        """
        # build pdl command line from properties
        self._properties['file'] = ''
        self._properties['directory'] = ''
        cmd = self._pdlcmd

        # make this a delete status
        cmd = cmd.replace('[STATUS]', 'DELETE')

        # fill out the required properties
        cmd = self._replace_required_properties(cmd)

        # fill out any files or directories we'll be sending
        cmd = self._replace_files(cmd)

        # fill in all the product properties
        cmd = self._replace_product_properties(cmd)

        # fill in all the optional properties
        cmd = self._replace_optional_properties(cmd)

        retcode, stdout, stderr = get_command_output(cmd)
        if not retcode:
            ptype = self._properties['type']
            fmt = (f'Could not delete product "{ptype}" due to error '
                   f'"{stdout + stderr}"')
            raise PDLError(fmt)

        return stdout
