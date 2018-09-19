#!/usr/bin/env python

# stdlib imports
import os.path
import datetime

# third party

# local
from .sender import Sender

# local imports
from impactutils.io.cmd import get_command_output

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
            raise Exception('For PDL, you may only send one file at a time.')

        # build pdl command line from properties
        cmd = self._pdlcmd
        for propkey in self._required_properties:
            propvalue = self._properties[propkey]
            cmd = cmd.replace('[' + propkey.upper() + ']', propvalue)
        cmd = cmd.replace('[STATUS]', 'UPDATE')
        if self._local_files:
            cmd = cmd.replace('[FILE]', '--file=%s' % (self._local_files[0]))
        else:
            cmd = cmd.replace('[FILE]', '')
        if self._local_directory:
            cmd = cmd.replace('[DIRECTORY]', '--directory=%s' %
                              (self._local_directory))
        else:
            cmd = cmd.replace('[DIRECTORY]', '')

        # add product properties as --property-PROPKEY=PROPVALUE
        prop_nuggets = []
        for propkey, propvalue in self._product_properties.items():
            if isinstance(propvalue, float):
                prop_nuggets.append('--property-%s=%.4f' %
                                    (propkey, propvalue))
            elif isinstance(propvalue, int):
                prop_nuggets.append('--property-%s=%i' % (propkey, propvalue))
            elif isinstance(propvalue, datetime.datetime):
                prop_nuggets.append(
                    '--property-%s=%s'
                    % (propkey, propvalue.strftime(DATE_TIME_FMT)[0:23]))
            elif isinstance(propvalue, str):
                prop_nuggets.append('--property-%s="%s"' %
                                    (propkey, propvalue))
            else:
                prop_nuggets.append('--property-%s=%s' %
                                    (propkey, str(propvalue)))
        cmd = cmd.replace('[PRODUCT_PROPERTIES]', ' '.join(prop_nuggets))

        # add optional properties
        opt_nuggets = []
        for propkey in self._optional_properties:
            if propkey in self._properties:
                if propkey == 'eventtime':
                    opt_nuggets.append(
                        '--%s=%sZ'
                        % (propkey,
                           self._properties[propkey].strftime(DATE_TIME_FMT)[0:23]))
                else:
                    fmt = '--%s=' + self._optional_properties_fmt[propkey]
                    opt_nuggets.append(
                        fmt % (propkey, self._properties[propkey]))
        cmd = cmd.replace('[OPTIONAL_PROPERTIES]', ' '.join(opt_nuggets))

        # call PDL on the command line
        retcode, stdout, stderr = get_command_output(cmd)
        if not retcode:
            fmt = 'Could not send product "%s" due to error "%s"'
            tpl = (retcode, stdout + stderr)
            raise Exception(fmt % tpl)

        # return the number of files we just sent
        nfiles = 0
        if self._local_files:
            nfiles += 1
        if self._local_directory:
            nfiles += sum([len(files)
                           for r, d, files in os.walk(self._local_directory)])

        msg = '%i files sent successfully: resulting in output: "%s"' % (
            nfiles, stdout.decode('utf-8'))
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
        self._properties['status'] = 'DELETE'
        self._properties['file'] = ''
        self._properties['directory'] = ''
        cmd = self._pdlcmd
        for propkey, propvalue in self._properties.items():
            cmd = cmd.replace('[' + propkey.upper() + ']', propvalue)

        retcode, stdout, stderr = get_command_output(cmd)
        if not retcode:
            fmt = 'Could not delete product "%s" due to error "%s"'
            tpl = (code, stdout + stderr)
            raise Exception(fmt % tpl)

        return stdout
