#stdlib imports
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

MAX_BCC = 25 #not sure what this really is...
DEFAULT_CANCEL_MSG = 'This is a cancel message.'

class EmailSender(Sender):
    '''Class for sending files via email to any number of recipients.
    
    EmailSender will send any number (within email server file size attachment limits) of files and/or
    directories to a set of recipients.  The file attachments can be zipped together into a single .zip 
    file attachment.  If you are sending more than one file, creating a zip file is HIGHLY recommended.

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

    Required properties:
      - smtp_servers List of strings indicating hostnames for SMTP servers to which you have permissions to connect.
      - sender Email address which will appear in the From: field in the recipient's email.
      - subject String containing the email subject line.
      - recipients List of valid email addresses to which message will be sent.
      - message Message which will be sent.
    '''
    _required_properties = ['smtp_servers','sender',
                            'subject','recipients','message']
                            
    _optional_properties = ['zip_file']
    def send(self):
        """
        Send a message to intended recipients with or without attachment.

        This method should determine the MIME type of the attachment and
        insert it into the message, along with the specified text.

        :raises:
          Exception when:
           - Attachment is not a valid file.
           - There is one of a number of errors connecting to email servers.
        """
        tempdir = tempfile.mkdtemp()
        zip_file = None
        if 'zip_file' in self._properties:
            zip_file = self._properties['zip_file']
        sender = self._properties['sender']
        subject = self._properties['subject']
        text = self._properties['message']
        smtp_servers = self._properties['smtp_servers']
        #send email to all recipients, attaching files as necessary or zipping into one file to
        #be attached.
        try:
            address_tuples = _split_addresses(self._properties['recipients'])
            attachments = []
            
            for address,bcc in address_tuples:
                if len(self._local_files) or self._local_directory:
                    if zip_file is not None:
                        #create a zip file with all of the contents
                        zfilename = os.path.join(tempdir,zip_file)
                        myzip = zipfile.ZipFile(zfilename,'w',compression=zipfile.ZIP_DEFLATED)
                        for filename in self._local_files:
                            root,arcname = os.path.split(filename)
                            myzip.write(filename,arcname)
                        if self._local_directory:
                            allfiles = self.getAllLocalFiles()
                            for filename in allfiles:
                                arcname = filename.replace(self._local_directory,'')
                                myzip.write(filename,arcname)
                        myzip.close()
                        attachments.append(zfilename)
                    else:
                        for filename in self._local_files:
                            attachments.append(filename)
                        
                            all_files = self.getAllLocalFiles()
                        for filename in all_files:
                            attachments.append(filename)
                        
                if not len(attachments):
                    msg = MIMEText(text)
                    msg['From'] = sender
                    msg['To'] = address
                    msg['Subject'] = subject
                    msg['Date'] = email.utils.formatdate() 
                    if bcc is not None:
                        bccstr = ', '.join(bcc)
                        msg['Bcc'] = bccstr
                        msgtxt = msg.as_string()
                else:
                    msgtxt = _get_encoded_message(address,subject,text,sender,attachments,bcc=bcc)
                all_addresses = [address] + bcc
                _send_email(sender,all_addresses,msgtxt,smtp_servers)
        except Exception as e:
            raise Exception('Could not send mail to %s with EmailSender. "%s"' % (address,str(e)))
        finally:
            shutil.rmtree(tempdir)
        nfiles = len(self._local_files)
        nfiles += sum([len(files) for r, d, files in os.walk(self._local_directory)])
        fmt = '%i files successfully sent to %i recipients.'
        return (nfiles,fmt % (nfiles,len(self._properties['recipients'])))

    def cancel(self,cancel_content=None):
        """Send a cancel message to list of recipients.

        :param cancel_content:
          String containing text that should be sent to recipients (default 'This is a cancel message.')/
        :returns:
          A string message describing what has occurred.
        """
        #send a cancel message to all recipients
        sender = self._properties['sender']
        subject = self._properties['subject']
        text = cancel_content
        address_tuples = _split_addresses(self._properties['recipients'])
        smtp_servers = self._properties['smtp_servers']
        attachments = []
        if cancel_content is None:
            cancel_content = DEFAULT_CANCEL_MSG
        for address,bcc in address_tuples:
            msg = MIMEText(cancel_content)
            msg['From'] = sender
            msg['To'] = address
            msg['Subject'] = subject
            msg['Date'] = email.utils.formatdate() 
            bccstr = ', '.join(bcc)
            msg['Bcc'] = bccstr
            msgtxt = msg.as_string()
            all_addresses = [address] + bcc
            _send_email(sender,all_addresses,msgtxt,smtp_servers)
            
def _split_addresses(recipients):
    """Split addresses into a list of tuples of (recipient,bcclist).

    :param recipients:
      List of intended email recipients.
    :returns:
      List of tuples, where each tuple consists of:
        - Email recipient.
        - list of recipients who will be bcc'd on the email to the first recipient.
    """
    MAX_BCC = 5
    tuples = []
    istart = 0
    iend = MAX_BCC
    while istart < len(recipients):
        address = recipients[istart]
        iend = min(len(recipients),istart+MAX_BCC)
        bcclist = recipients[istart+1:iend]
        tuples.append((address,bcclist))
        istart = iend + 1
        
    return tuples
    
def _send_email(sender,address,msgtxt,smtp_servers):
    """Send email to given address(es).

    :param sender:
      From email address.
    :param address:
      Single email address or list of addresses.
    :param msgtxt:
      MIMEText email message encoded as a string.
    :param smtp_servers:
      List of smtp servers to try to send from.
    :raises:
      Exception if sending the message failed for any reason.
    """
    messageSent = False
    errormsg = []
    #let's try all of the email servers we know about before
    #admitting defeat...
    for server in smtp_servers:
        #print 'Trying server %s' % (server)
        try:
            session = smtplib.SMTP(server)
            session.sendmail(sender,address, msgtxt)
            messageSent = True
            session.quit()
            break
        except smtplib.SMTPRecipientsRefused:
            errormsg.append({server:'Recipients refused'})
            continue
        except smtplib.SMTPHeloError:
            errormsg.append({server:'Server did not respond to hello'})
            continue
        except smtplib.SMTPSenderRefused:
            errormsg.append({server:'Server refused sender address'})
            continue
        except smtplib.SMTPDataError:
            errormsg.append({server:'Server responded with an unexpected error code'})
            continue
        except:
            errormsg.append({server:'Connection to server failed (possible timeout)'})

    if not messageSent:
        errstr = 'The message to %s was not sent.  The server error messages are below:' % (address)
        for errdict in errormsg:
            errstr = errstr + str(errdict)
        raise Exception(str(errstr))

    print('Message sent to "%s"' % address)
    # if bcc is not None:
    #     print('Bcc: %s' % ','.join(bcc))
        
def _get_encoded_message(address,subject,text,sender,attachments,bcc=None):
    """Private method for encoding attachment into a MIME string.

    :param address:
      Primary (not Bcc) email recipient.
    :param subject:
      String email subject line.
    :param text:
      String text of email message.
    :param attachments:
      List of files to be attached to message.
    :param bcc:
      List of email addresses to Bcc:
    :returns:
      Message text.
    """
    outer = MIMEMultipart()
    outer['Subject'] = subject
    outer['To'] = address
    outer['From'] = sender
    outer['Date'] = email.utils.formatdate()
    if bcc is not None:
        outer['Bcc'] = ', '.join(bcc)

    #insert the text into the email as a MIMEText part...
    firstSubMsg=Message()
    firstSubMsg["Content-type"]="text/plain"
    firstSubMsg["Content-transfer-encoding"]="7bit"
    firstSubMsg.set_payload(text)
    outer.attach(firstSubMsg)

    for attachment in attachments:
        #outer.preamble = 'You will not see this in a MIME-aware mail reader.\n'
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
            #Encode the payload using Base64
            encoders.encode_base64(msg)

        msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment))
        outer.attach(msg)

    return outer.as_string()
