#!/usr/bin/env python
import base64
import getpass
import logging
from optparse import OptionParser

from bisque import BisqueConnection
import imeta
import iquest
import iutils

IRODS_DEFAULT_HOST='irods://lmu-omero1.biocenter.helsinki.fi'
BISQUE_DEFAULT_HOST='http://lmu-omero1.biocenter.helsinki.fi:8000'

logger = logging.getLogger(__name__)

usage = """%prog [options] irods_data

Register files from an irods repository with a bisque server.
See %prog -h for options.
"""
def main():
    irods_host = IRODS_DEFAULT_HOST
    bisque_host = BISQUE_DEFAULT_HOST

    parser = OptionParser(usage=usage)
    parser.add_option('-l', '--list', action="store_true", default=False, 
                      help="list contents of irods url and exit")
    parser.add_option('-n', '--dryrun', action="store_true", default=False, 
                      help="print actions but do not execute.. sets verbose")
    parser.add_option('-i', '--irods_host', help="e.g. irods://ida.csc.fi")
    parser.add_option('-b', '--bisque_host', help="e.g. https://bisquevm-1.it.helsinki.fi")
    parser.add_option('-v', '--verbose', action="store_true", default=False, help="be verbose")
    options, args = parser.parse_args()
    if len(args)>0:
        irods_data = args.pop(0)
    else:
        parser.error("No irods data given.")
    
    # set log level
    if options.verbose:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    elif options.dryrun:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.CRITICAL)

    # check server URLs
    if options.irods_host:
        irods_host = options.irods_host
    if not irods_host or not  irods_host.startswith('irods://'):
        parser.error ('must include a valid iRODS url i.e. %s' % IRODS_DEFAULT_HOST)
    if options.bisque_host:
        irods_host = options.bisque_host
    if not bisque_host or not  (bisque_host.startswith('http://') or bisque_host.startswith('https://') ):
        parser.error ("Invalid Bisque host URL '%s'.\nPlease specify valid HTTP URL i.e. '%s'." % (bisque_host,  BISQUE_DEFAULT_HOST))
    if bisque_host.startswith('http://') :
        logging.warning("Using plain HTTP, passwords will be sent unencrypted.")

    DATA_IS_COLLECTION = False
    DATA_IS_SINGLE_OBJECT = False
    # check if user specified a collection or a single dataobject
    DATA_IS_COLLECTION = iquest.collection_exists(irods_data)
    if not DATA_IS_COLLECTION:
        DATA_IS_SINGLE_OBJECT = iquest.dataobject_exists(irods_data)
    # check if the collection or data exists
    if not  DATA_IS_COLLECTION and not DATA_IS_SINGLE_OBJECT:
        # user probably didn't give full path starting from /ZONE/home/...
        # try in the current irods directory
        irods_data_orig = irods_data
        iutils.icd2ipwd()
        root = iutils.ipwd()
        irods_data = root + "/" + irods_data
        DATA_IS_COLLECTION = iquest.collection_exists(irods_data)
        if not DATA_IS_COLLECTION:
            DATA_IS_SINGLE_OBJECT = iquest.dataobject_exists(irods_data)
        if not  DATA_IS_COLLECTION and not DATA_IS_SINGLE_OBJECT:
            parser.error("File or collection '" + irods_data_orig + "' not found in " + irods_host + ".")

    if DATA_IS_COLLECTION:
        entries = iquest.list_dataobjects_recursive(irods_data)
    else:
        entries = []
        entries.append(irods_data)
        
    if options.list:
        for e in entries:
            print e
        return
    
    
    # ask user for bisque username/password
    print
    print "Please login to Bisque with your University AD username and password."
    bisque_user = getpass.getuser()
    print "Username:", bisque_user
    bisque_password = getpass.getpass()
    if not bisque_user or not bisque_password:
        parser.error('Username/password needs to be provided for uploads.')

    bisque = BisqueConnection(bisque_host, bisque_user, bisque_password)
    for irods_file in entries:
        bisque.register_irods_file(irods_host,  irods_file,  options.dryrun)

if __name__ == "__main__":
    main()
