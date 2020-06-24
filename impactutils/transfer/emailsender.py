# stdlib imports
import os.path
import shutil
import smtplib
import mimetypes
from email import encoders
from email.message import Message
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import email.utils
import tempfile
import zipfile

# local
from .sender import Sender

# default maximum number of bcc email addresses per message.
# Not sure what this is normally set to on typical SMTP server,
# so being conservative here
MAX_BCC = 25
DEFAULT_CANCEL_MSG = 'This is a cancel message.'


class EmailSender(Sender):
    '''Class for sending files via email to any number of recipients.

    EmailSender will send any number (within email server file size attachment
    limits) of files and/or directories to a set of recipients.  The file
    attachments can be zipped together into a single .zip  file attachment.
    If you are sending more than one file, creating a zip file is HIGHLY
    recommended.

    By default, the emails will be sent using Bcc lists of 25, meaning that a
    email messages to multiple recipients will be sent to one person, with 25
    Bcc recipients.  This value can be  changed with the optional max_bcc
    property.  If you do not happen to control the SMTP server through which
    you are sending emails, or know what its settings are, it is best (in the
    author's opinion) to be conservative in setting this value.

    To send a file to a list of email recipients:
    props = {}
    props['recipients'] = ['fred@foo.com','barney@bar.org']
    props['smtp_servers'] = [my.smtp.server.org]
    props['sender'] = 'mrslate@quarry.org'
    props['subject'] = "You're fired!"
    props['message'] = 'You two idiots are thicker than the rocks you break!'

    sender = EmailSender(properties=props,local_files=['/home/mrslate/hammer.gif'])
    sender.send()

    To send a cancel message to the same list of email recipients:
    sender.cancel(cancel_content='Never mind - I like the way you guys work.')

    To send a zipped directory to the same list of email recipients:
    props = {}
    props['recipients'] = ['fred@foo.com','barney@bar.org']
    props['smtp_servers'] = [my.smtp.server.org]
    props['sender'] = 'mrslate@quarry.org'
    props['subject'] = "You're fired!"
    props['message'] = 'You two idiots are thicker than the rocks you break!'
    props['zip_file'] = 'allfiles.zip'
    sender = EmailSender(properties=props,local_directory='/home/mrslate/termination_docs'])
    sender.send()

    To send individual email messages (not using Bcc functionality) to a
    number of recipients:
    props = {}
    props['recipients'] = ['fred@foo.com','barney@bar.org']
    props['smtp_servers'] = [my.smtp.server.org]
    props['sender'] = 'mrslate@quarry.org'
    props['subject'] = "You're fired!"
    props['message'] = 'You two idiots are thicker than the rocks you break!'
    props['max_bcc'] = 0

    To send batch email messages (using Bcc functionality), preserving
    anonymity betweeen recipients by using the sender as the primary recipient:
    props = {}
    props['recipients'] = ['fred@foo.com','barney@bar.org']
    props['smtp_servers'] = [my.smtp.server.org]
    props['sender'] = 'mrslate@quarry.org'
    props['subject'] = "You're fired!"
    props['message'] = 'You two idiots are thicker than the rocks you break!'
    props['max_bcc'] = 25

    To send batch email messages (using Bcc functionality), preserving
    anonymity betweeen recipients by setting the primary_recipient property:
    props = {}
    props['recipients'] = ['fred@foo.com','barney@bar.org']
    props['smtp_servers'] = [my.smtp.server.org]
    props['sender'] = 'mrslate@quarry.org'
    props['subject'] = "You're fired!"
    props['message'] = 'You two idiots are thicker than the rocks you break!'
    props['primary_recipient'] = 'employees@quarry.org'
    props['max_bcc'] = 25

    Required properties:
      - smtp_servers List of strings indicating hostnames for SMTP servers to
        which you have permissions to connect.
      - sender Email address which will appear in the From: field in the
        recipient's email.
      - subject String containing the email subject line.
      - recipients List of valid email addresses to which message will be sent.
      - message Message which will be sent.
    Optional properties:
      -
    '''
    _required_properties = ['smtp_servers', 'sender',
                            'subject', 'recipients', 'message']

    _optional_properties = ['zip_file', 'max_bcc']

    def send(self):
        """
        Send a message to intended recipients with or without attachment.

        This method should determine the MIME type of the attachment and
        insert it into the message, along with the specified text.

        Raises:
          Exception when:
           - Attachment is not a valid file.
           - There is one of a number of errors connecting to email servers.
        """
        tempdir = tempfile.mkdtemp()
        zip_file = None
        if 'zip_file' in self._properties:
            zip_file = self._properties['zip_file']
        max_bcc = MAX_BCC
        if 'max_bcc' in self._properties:
            max_bcc = self._properties['max_bcc']

        # if using Bcc, try to maintain privacy between recipients by using
        # either an empty string (default) or use the primary_recipient
        # property, if set.
        primary_recipient = None
        if max_bcc:
            if 'primary_recipient' in self._properties:
                primary_recipient = self._properties['primary_recipient']
            else:
                primary_recipient = ''

        sender = self._properties['sender']
        subject = self._properties['subject']
        text = self._properties['message']
        smtp_servers = self._properties['smtp_servers']
        # send email to all recipients, attaching files as necessary or zipping
        # into one file to be attached.
        try:
            address_tuples = _split_addresses(
                self._properties['recipients'], max_bcc,
                primary_recipient)

            for address, bcc in address_tuples:
                attachments = []
                if len(self._local_files) or self._local_directory:
                    if zip_file is not None:
                        # create a zip file with all of the contents
                        zfilename = os.path.join(tempdir, zip_file)
                        myzip = zipfile.ZipFile(
                            zfilename, 'w', compression=zipfile.ZIP_DEFLATED)
                        for filename in self._local_files:
                            root, arcname = os.path.split(filename)
                            myzip.write(filename, arcname)
                        if self._local_directory:
                            allfiles = self.getAllLocalFiles()
                            for filename in allfiles:
                                arcname = filename.replace(
                                    self._local_directory, '')
                                myzip.write(filename, arcname)
                        myzip.close()
                        attachments.append(zfilename)
                    else:
                        for filename in self._local_files:
                            attachments.append(filename)

                            all_files = self.getAllLocalFiles()
                        for filename in all_files:
                            attachments.append(filename)

                if not len(attachments):
                    msg = MIMEText(text, "utf-8")
                    msg['From'] = sender
                    msg['To'] = address
                    msg['Subject'] = subject
                    msg['Date'] = email.utils.formatdate()
                    if bcc is not None:
                        bccstr = ', '.join(bcc)
                        msg['Bcc'] = bccstr
                    msgtxt = msg.as_string()
                else:
                    msgtxt = _get_encoded_message(
                        address, subject, text, sender, attachments, bcc=bcc)
                if bcc is not None:
                    all_addresses = [address] + bcc
                else:
                    all_addresses = [address]
                _send_email(sender, all_addresses, msgtxt, smtp_servers)
        except Exception as e:
            raise Exception(
                f'Could not send mail to {address} with EmailSender. "{str(e)}"')
        finally:
            shutil.rmtree(tempdir)
        nfiles = len(self._local_files)
        if self._local_directory is not None:
            nfiles += sum([len(files)
                           for r, d, files in os.walk(self._local_directory)])
        num_files = int(nfiles)
        num_recipients = int(len(self._properties['recipients']))
        fmt = f'{num_files:d} files successfully sent to {num_recipients:d} recipients.'
        return (nfiles, fmt)

    def cancel(self, cancel_content=None):
        """Send a cancel message to list of recipients.

        Args:
            cancel_content: String containing text that should be sent to
                recipients (default 'This is a cancel message.')

        Returns:
            A string message describing what has occurred.
        """
        # send a cancel message to all recipients
        sender = self._properties['sender']
        subject = self._properties['subject']

        max_bcc = MAX_BCC
        if 'max_bcc' in self._properties:
            max_bcc = self._properties['max_bcc']

         # if using Bcc, try to maintain privacy between recipients by using
        # either an empty string (default) or use the primary_recipient
        # property, if set.
        primary_recipient = None
        if max_bcc:
            if 'primary_recipient' in self._properties:
                primary_recipient = self._properties['primary_recipient']
            else:
                primary_recipient = ''

        address_tuples = _split_addresses(self._properties['recipients'],
                                          max_bcc,
                                          primary_recipient)
        smtp_servers = self._properties['smtp_servers']
        if cancel_content is None:
            cancel_content = DEFAULT_CANCEL_MSG
        for address, bcc in address_tuples:
            msg = MIMEText(cancel_content)
            msg['From'] = sender
            msg['To'] = address
            msg['Subject'] = subject
            msg['Date'] = email.utils.formatdate()
            bccstr = ', '.join(bcc)
            msg['Bcc'] = bccstr
            msgtxt = msg.as_string()
            all_addresses = [address] + bcc
            _send_email(sender, all_addresses, msgtxt, smtp_servers)


def _split_addresses(recipients, max_bcc, primary_recipient):
    """Split addresses into a list of tuples of (recipient,bcclist).

    Args:
        recipients: List of intended email recipients.

    Returns:
        List of tuples, where each tuple consists of:
        - Email recipient.
        - list of recipients who will be bcc'd on the email to the first
          recipient.
    """

    tuples = []
    if max_bcc == 0:
        for recipient in recipients:
            tuples.append((recipient, []))
        return tuples
    istart = 0
    iend = max_bcc
    while istart < len(recipients):
        address = primary_recipient
        iend = min(len(recipients), istart + (max_bcc - 1))
        bcclist = recipients[istart:iend]
        tuples.append((address, bcclist))
        istart = iend

    return tuples


def _send_email(sender, address, msgtxt, smtp_servers):
    """Send email to given address(es).

    Args:
        sender: From email address.
        address: Single email address or list of addresses.
        msgtxt: MIMEText email message encoded as a string.
        smtp_servers: List of smtp servers to try to send from.

    Raises:
        Exception if sending the message failed for any reason.
    """
    messageSent = False
    errormsg = []
    # let's try all of the email servers we know about before
    # admitting defeat...
    servername = ''
    for server in smtp_servers:
        # print 'Trying server %s' % (server)
        try:
            session = smtplib.SMTP(server)
            resp, servername = session.helo()
            session.sendmail(sender, address, msgtxt)
            messageSent = True
            session.quit()
            break
        except smtplib.SMTPRecipientsRefused:
            errormsg.append({server: 'Recipients refused'})
            continue
        except smtplib.SMTPHeloError:
            errormsg.append({server: 'Server did not respond to hello'})
            continue
        except smtplib.SMTPSenderRefused:
            errormsg.append({server: 'Server refused sender address'})
            continue
        except smtplib.SMTPDataError:
            errormsg.append(
                {server: 'Server responded with an unexpected error code'})
            continue
        except:
            errormsg.append(
                {server: 'Connection to server failed (possible timeout)'})

    if not messageSent:
        errstr = (f'The message to {address} was not sent. '
                  'The server error messages are below:')
        for errdict in errormsg:
            errstr = errstr + str(errdict)
        raise Exception(str(errstr))

    print(f'Message sent to "{address}" via SMTP server "{servername}"')
    # if bcc is not None:
    #     print('Bcc: %s' % ','.join(bcc))


def _get_encoded_message(address, subject, text, sender, attachments,
                         bcc=None):
    """Private method for encoding attachment into a MIME string.

    Args:
        address: Primary (not Bcc) email recipient.
        subject: String email subject line.
        text: String text of email message.
        attachments: List of files to be attached to message.
        bcc: List of email addresses to Bcc.

    Returns:
        Message text.
    """
    outer = MIMEMultipart()
    outer['Subject'] = subject
    outer['To'] = address
    outer['From'] = sender
    outer['Date'] = email.utils.formatdate()
    if bcc is not None:
        outer['Bcc'] = ', '.join(bcc)

    # insert the text into the email as a MIMEText part...
    # firstSubMsg = Message()
    # firstSubMsg["Content-type"] = "text/plain"
    # firstSubMsg["Content-transfer-encoding"] = "7bit"
    # firstSubMsg.set_payload(text)
    firstSubMsg = MIMEText(text)
    outer.attach(firstSubMsg)

    for attachment in attachments:
        ctype, encoding = mimetypes.guess_type(attachment)
        msg = None
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        if maintype == 'text':
            fp = open(attachment)
            # Note: we should handle calculating the charset
            msg = MIMEText(fp.read(), _subtype=subtype)
            fp.close()
        elif maintype == 'image':
            fp = open(attachment, 'rb')
            msg = MIMEImage(fp.read(), _subtype=subtype)
            fp.close()
        elif maintype == 'audio':
            fp = open(attachment, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=subtype)
            fp.close()
        elif maintype == 'application':
            fp = open(attachment, 'rb')
            msg = MIMEApplication(fp.read(), _subtype=subtype)
            fp.close()
        else:
            fp = open(attachment, 'rb')
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(fp.read())
            fp.close()
            # Encode the payload using Base64
            encoders.encode_base64(msg)

        msg.add_header('Content-Disposition', 'attachment',
                       filename=os.path.basename(attachment))
        outer.attach(msg)

    return outer.as_string()
