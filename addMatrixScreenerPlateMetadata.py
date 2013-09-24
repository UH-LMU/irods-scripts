#!/usr/bin/env python
import glob
import logging
from optparse import OptionParser
import os
import os.path
import re
import subprocess
import sys

from createCollectionMetadataTemplate import DEFAULT_COLL_META_TEMPLATE
import imeta
import iquest
import iutils

usage ="""%prog [options] target

Add MatrixScreener plate metadata to ome.tif files in the target folder. 
Run '%prog -h' for options.
"""

ATTR_DATASET = "HCS.Dataset"
ATTR_WELL = "HCS.Well"
ATTR_FIELD = "HCS.Field"
ATTR_CHANNEL = "HCS.Channel"

rows = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']

reOME = re.compile('image--L([0-9]+)--S([0-9]+)--U([0-9]+)--V([0-9]+)--J([0-9]+)--E([0-9]+)--O([0-9]+)--X([0-9]+)--Y([0-9]+)--T([0-9]+)--Z([0-9]+)--C([0-9]+).ome.tif')
reOMEfield = re.compile('image--L([0-9]+)--S([0-9]+)--U([0-9]+)--V([0-9]+)--J([0-9]+)--E([0-9]+)--O([0-9]+)--X([0-9]+)--Y([0-9]+)')
reExp = re.compile('experiment--[0-9][0-9][0-9][0-9]_[0-9][0-9]_[0-9][0-9]_[0-9][0-9]_[0-9][0-9]_[0-9][0-9]')

def createDatasetCode(target):
    result = reExp.search(target)
    return result.group(0)

def createWellCode(u, v):
    col = repr(int(u) + 1).zfill(2)
    row = rows[v]
    return row + col

def createFieldIndex(x, y):
    return x + ',' + y

def main():
    parser = OptionParser(usage=usage)
    parser.add_option('-n', '--dryrun', action="store_true", default=False, help="Print actions but do not execute.")
    parser.add_option('-v', '--verbose', action="store_true", default=False, help="")
    parser.add_option('-x', '--offsetx', type="int", help="")
    parser.add_option('-y', '--offsety', type="int", help="")

    options, args = parser.parse_args()
    
    # set log level
    if options.verbose:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    # use offsets if A01 is not the first well imaged
    # e.g. it first well is C4, set offsetx = 3, offsety = 2
    offsetx = 0
    offsety = 0
    if options.offsetx:
        offsetx = options.offsetx
    if options.offsety:
        offsety = options.offsety

    
    # When the python script is started, it has own new shell, with a new irods environment
    # where the current working directory is ~. 
    # This command checks the current working directory of the parent shell from the .irodsEnv files.
    iutils.icd2ipwd()
    ipwd= iutils.ipwd()

    target = None
    # check if template was given
    if len(args) == 0:
        parser.error("No target folder given.")
    else:
        target = args[0]

    # check if template is an absolute path
    if iquest.collection_exists(ipwd + "/" + target):
        target = ipwd + "/" + target
    else:
        if not iquest.collection_exists(target):
            parser.error("Target " + target + " not found.")
    logging.info("Target folder " + target)

    dataset = createDatasetCode(target)

    files = iquest.list_dataobjects_recursive(target)
    for f in files:
        # for originals and converted hyperstacks
        result = reOMEfield.search(f)
        if result:
            logging.debug(f)
            # read Matrix Screener indexes
            u = result.group(3)
            v = result.group(4)
            x = result.group(8)
            y = result.group(9)
            
            # apply offsets
            u = int(u) + offsetx
            v = int(v) + offsety
            
            avu = imeta.AVU(ATTR_DATASET, dataset)
            logging.debug('dataset:{0}'.format(dataset))
            if not options.dryrun:
                imeta.delete(f,avu)
                imeta.add(f,avu)

            well = createWellCode(u, v)
            logging.debug('U:{0}, V:{1}, well:{2}'.format(u, v, well))
            avu = imeta.AVU(ATTR_WELL,  well)
            if not options.dryrun:
                imeta.delete(f, avu)
                imeta.add(f, avu)
            
            field = createFieldIndex(x, y)
            logging.debug("field: " + field)
            avu = imeta.AVU(ATTR_FIELD,  field)
            if not options.dryrun:
                imeta.delete(f, avu)
                imeta.add(f, avu)

        # for original MatrixScreener output
        result = reOME.search(f)
        if result:
            c = result.group(12)
            channel = str(int(c))
            logging.debug("channel: " + channel)
            avu = imeta.AVU(ATTR_CHANNEL, channel)
            if not options.dryrun:
                imeta.delete(f, avu)
                imeta.add(f, avu)



if __name__ == "__main__":
    main()

