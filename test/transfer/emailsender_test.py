#!/usr/bin/env python

# stdlib imports
import os.path
import shutil
import sys
import tempfile
from unittest import mock

# third party imports
import pytest

# local imports
from impactutils.transfer.emailsender import EmailSender


# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
# put this at the front of the system path, ignoring any installed mapio stuff
sys.path.insert(0, shakedir)


def test_mock_send():
    subject = 'Testing...'
    message = 'This is a test message.'
    cancel_msg = 'This is a cancel message.'
    zip_file = 'test.zip'
    props = {'smtp_servers': 'server',
             'sender': 'sender',
             'subject': 'subject',
             'recipients': ['recipients'],
             'message': 'message'}
    thisfile = os.path.abspath(__file__)  # where is this script?
    thisdir = os.path.dirname(os.path.abspath(
        __file__))  # what folder are we in?

    # send a file
    send = 'impactutils.transfer.emailsender._send_email'
    with mock.patch(send) as mock_send:
        # error code, stdout, stderr
        mock_send.return_value = ''
        sender = EmailSender(properties=props, local_files=[thisfile])
        sender.send()
        sender.cancel(cancel_content=cancel_msg)

    with mock.patch(send) as mock_send:
        props['zip_file'] = zip_file
        sender = EmailSender(properties=props, local_files=[thisfile])
        sender.send()
        sender.cancel(cancel_content=cancel_msg)


def send_test(smtp_servers, sender, recipients):
    subject = 'Testing...'
    message = 'This is a test message.'
    cancel_msg = 'This is a cancel message.'
    zip_file = 'test.zip'
    props = {'smtp_servers': smtp_servers,
             'sender': sender,
             'subject': subject,
             'recipients': recipients,
             'message': message}
    thisfile = os.path.abspath(__file__)  # where is this script?
    thisdir = os.path.dirname(os.path.abspath(
        __file__))  # what folder are we in?

    # send a file
    sender = EmailSender(properties=props, local_files=[thisfile])
    sender.send()
    sender.cancel(cancel_content=cancel_msg)

    # send a directory, and zip it
    props['zip_file'] = zip_file
    sender = EmailSender(properties=props, local_files=[thisfile])
    sender.send()
    sender.cancel(cancel_content=cancel_msg)


def bcc_test(smtp_server, sender, max_bcc, recipients, primary_recipient):
    if primary_recipient == 'null':
        primary_recipient = None
    if primary_recipient == 'empty':
        primary_recipient = ''
    subject = 'Testing...'
    message = 'This is a test message.'
    props = {'smtp_servers': [smtp_server],
             'sender': sender,
             'subject': subject,
             'recipients': recipients,
             'max_bcc': max_bcc,
             'primary_recipient': primary_recipient,
             'message': message}
    sender = EmailSender(properties=props)
    sent = sender.send()
    print(sent)


def test_exceptions():
    subject = 'Failed Testing...'
    message = 'This is a test message that will fail.'
    cancel_msg = 'This is a cancel message.'
    zip_file = 'test.zip'
    props = {'smtp_servers': [''],
             'sender': 'me',
             'subject': subject,
             'recipients': ['me', 'you'],
             'max_bcc': 3,
             'primary_recipient': 'them',
             'message': message}
    props2 = {'smtp_servers': [''],
              'sender': 'me',
              'subject': subject,
              'recipients': ['me', 'you'],
              'primary_recipient': 'them',
              'message': message}
    thisfile = os.path.abspath(__file__)  # where is this script?
    thisdir = os.path.dirname(os.path.abspath(
        __file__))  # what folder are we in?

    match_msg = "Connection to server failed"
    with pytest.raises(Exception, match=match_msg) as a:
        sender = EmailSender(properties=props)
        sender.send()

    with pytest.raises(Exception, match=match_msg) as a:
        sender = EmailSender(properties=props2)
        sender.send()

    with pytest.raises(Exception, match=match_msg) as a:
        sender = EmailSender(properties=props, local_files=[thisfile])
        sender.send()

    with pytest.raises(Exception, match=match_msg) as a:
        # send a directory, and zip it
        props['zip_file'] = zip_file
        sender = EmailSender(properties=props, local_files=[thisfile])
        sender.send()

    with pytest.raises(Exception, match=match_msg) as a:
        sender = EmailSender(properties=props, local_files=[thisfile])
        sender.cancel(cancel_content=cancel_msg)

    with pytest.raises(Exception, match=match_msg) as a:
        sender = EmailSender(properties=props2, local_files=[thisfile])
        sender.cancel(cancel_content=cancel_msg)

    match_msg = "Input file image.png could not be found"
    with pytest.raises(Exception, match=match_msg) as a:
        sender = EmailSender(properties=props, local_files=['image.png'])
        sender.send()


if __name__ == '__main__':
    test_exceptions()
    test_mock_send()
    if len(sys.argv) > 1:
        smtp_server = sys.argv[1]
        sender = sys.argv[2]
        max_bcc = int(sys.argv[3])
        primary_recipient = sys.argv[4]
        recipients = sys.argv[5:]
        # send_test([smtp_server],sender,recipients)
        bcc_test(smtp_server, sender, max_bcc, recipients, primary_recipient)
