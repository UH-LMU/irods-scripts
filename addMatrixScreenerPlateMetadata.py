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


ATTR_WELL = "Well"
ATTR_FIELD = "Field"

row_map = {'00':'A','01':'B', '02':'C', '03':'D', '04':'E', '05':'F', '06':'G', '07':'H' }
reOME = re.compile('image--L([0-9]+)--S([0-9]+)--U([0-9]+)--V([0-9]+)--J([0-9]+)--E([0-9]+)--O([0-9]+)--X([0-9]+)--Y([0-9]+)--T([0-9]+)--Z([0-9]+)--C([0-9]+).ome.tif')

def createWellCode(u, v):
    col = repr(int(u) + 1).zfill(2)
    row = row_map[v]
    return row + col

def createFieldIndex(x, y):
    return x + ',' + y

def main():
    parser = OptionParser(usage=usage)
    parser.add_option('-n', '--dryrun', action="store_true", default=False, help="Print actions but do not execute.")
    parser.add_option('-v', '--verbose', action="store_true", default=False, help="")

    options, args = parser.parse_args()
    
    # set log level
    if options.verbose:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    
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


    files = iquest.list_dataobjects_recursive(target)
    for f in files:
        result = reOME.search(f)
        if result:
            logging.debug(f)
            u = result.group(3)
            v = result.group(4)
            x = result.group(8)
            y = result.group(9)
            
            well = createWellCode(u, v)
            avu = imeta.AVU(ATTR_WELL,  well)
            imeta.delete(f, avu)
            imeta.add(f, avu)
            
            field = createFieldIndex(x, y)
            avu = imeta.AVU(ATTR_FIELD,  field)
            imeta.delete(f, avu)
            imeta.add(f, avu)



if __name__ == "__main__":
    main()

