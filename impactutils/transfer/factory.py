from .copysender import CopySender
from .ftpsender import FTPSender
from .pdlsender import PDLSender
from .securesender import SecureSender

    
def get_sender_class(transfer_type):
    """Class factory for generating Sender class.

    :param transfer_type:
      String indicating which of supported Sender classes to return:
        - copy CopySender
        - ftp FTPSender
        - pdl PDLSender
        - ssh SecureSender
    :raises KeyError:
      When transfer_type is not one of the above strings.
    :returns:
      One of the above children of the Sender class.
    """
    types = {'copy':CopySender,
             'ftp':FTPSender,
             'pdl':PDLSender,
             'ssh':SecureSender}
    if transfer_type not in types:
        raise KeyError('%s not a supported transfer type.' % transfer_type)
    else:
        return types[transfer_type]
