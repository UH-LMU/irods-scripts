#!/usr/bin/env python
import glob
import logging
from optparse import OptionParser
import os
import os.path
import subprocess
import sys

import imeta
import iquest
import iutils

usage ="""%prog [options]

Copy metadata from file 'collectionMetadataTemplate' to the current collection (iutils.ipwd) and subcollections. Repeat in subcollections.
Run '%prog -h' for options.
"""

# file used to store collection metadata
COLL_META_TEMPLATE = "collectionMetadataTemplate"

# attributes that are set by Ida
ATTRIBUTES_SET_BY_IDA = ["Contact",  "Metadata modified",  "Modified",  "Metadata identifier",  "Identifier.version",  "Identifier.series" ]

class CollectionVisitor:
    def visit(self, collection):
        print collection

class ApplyMetadataTemplateVisitor(CollectionVisitor):
    def __init__(self, options):
        self.options = options
        
    def visit(self,  collection):
        # use user-provided a template file, if none given, look for default files.
        template = None
        if self.options.template:
            template = self.options.template
        else:
            logging.info("Using default template file 'collectionMetadataTemplate'.")
            test = collection + "/" + COLL_META_TEMPLATE
            if iquest.dataobject_exists(test):
                template = test
        
        if not template:
            logging.error("No template object found.")
            return
                
        if not iquest.dataobject_has_metadata(template):
            logging.error("Template object " + template + " has no metadata.")
            return

        # get the target dataobjects
        if self.options.recursive:
            dataobjects = iquest.list_dataobjects_recursive(collection)
        else:
            dataobjects =  iquest.list_dataobjects(collection)

        # get avus of the template object
        avus = iquest.get_metadata(template)
        
        for target in dataobjects:
            (head, tail) = os.path.split(target)
            # don't touch template files
            if  tail != COLL_META_TEMPLATE and target != template:
                for avu in avus:
                    # don't touch metadata set by Ida
                    if avu.a not in ATTRIBUTES_SET_BY_IDA:
                        if self.options.delete:
                            imeta.delete(target, avu,  self.options.dryrun)
                        else:
                            imeta.delete(target, avu,  self.options.dryrun)
                            imeta.copy(template,  target,  self.options.dryrun)


def Walk(root,  visitor):
    # process this collections
    visitor.visit(root)
    
    # recursion to subcollections
    if iquest.child_collections_exist(root):
        collections = iquest.list_child_collections(root)
        for c in collections:
            Walk(c,  visitor)
    
    

def main():
    parser = OptionParser(usage=usage)
    parser.add_option('-a', '--template',  help='iRODS file with template metadata (default ./collectionMetadataTemplate).')
    parser.add_option('-b', '--target',  help='iRODS file or collection where metadata will be copied (default `ipwd`).')
    parser.add_option('-r', '--recursive', action="store_true", default=False, help="Process also subcollections.")
    parser.add_option('-R', '--extra_recursive', action="store_true", default=False, help="Apply metadata from 'collectionMetadataTemplate' files in subcollections.")
    parser.add_option('-d', '--delete', action="store_true", default=False, help="Delete template file metadata attributes from the target.")
    parser.add_option('-n', '--dryrun', action="store_true", default=False, help="Print actions but do not execute.")
    parser.add_option('-v', '--verbose', action="store_true", default=False, help="")
    parser.add_option('-V', '--very_verbose', action="store_true", default=False, help="")

    options, args = parser.parse_args()
    
    # set log level
    if options.very_verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif options.dryrun or options.verbose:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)
    
    # if no target collection given, use the current iRODS working directory
    if not options.target:
        # When the python script is started, it has own new shell, with a new irods environment
        # where the current working directory is ~. 
        # This command checks the current working directory of the parent shell from the .irodsEnv files.
        iutils.icd2ipwd()
        options.target = iutils.ipwd()
        logging.warning("Using current iRODS working directory (" + options.target + ") as target.")
   
    visitor = ApplyMetadataTemplateVisitor(options)
    #visitor = CollectionVisitor()
    if options.extra_recursive:
        Walk(options.target,  visitor)
    else:
        visitor.visit(options.target)
    

if __name__ == "__main__":
    main()


    
