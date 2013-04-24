#!/usr/bin/env python
import glob
import logging
from optparse import OptionParser
import os
import os.path
import subprocess
import sys

from createCollectionMetadataTemplate import DEFAULT_COLL_META_TEMPLATE
import imeta
import iquest
import iutils

usage ="""%prog [options]

Copy metadata from a template to a target. 
- the target can be a single data object or a collection. 
- the default target is the current collection (ipwd).
Run '%prog -h' for options.
"""


# attributes that are set by Ida
# http://www.csc.fi/sivut/ida/ohjeet/kayttoohjeet/Kuvailuvaatimus
ATTRIBUTES_SET_BY_IDA = ["Metadata.identifier",  "Metadata.modified",  "Identifier.version",  "Identifier.series",  "Modified",  \
                         "Contact.type", "Contact.name",  "Contact.email",  "Contact.phone",  \
                         "Project.name",  "Project.funder",  "Project.funder_grant_number",  "Uploader"  ]
MISSING_METADATA = "MISSING_METADATA"

def addMetadata2DataObject(avus,  target,  dryrun):
    for avu in avus:
        # don't touch metadata set by Ida
        if avu.a not in ATTRIBUTES_SET_BY_IDA and avu.v != MISSING_METADATA:
            imeta.delete(target, avu,  dryrun)
            imeta.add(target, avu, dryrun)

def deleteMetadataFromDataObject(avus,  target,  dryrun):
    for avu in avus:
        # don't touch metadata set by Ida
        if avu.a not in ATTRIBUTES_SET_BY_IDA and avu.b != MISSING_METADATA:
            imeta.delete(target, avu,  dryrun)

class CollectionVisitor:
    def visit(self, collection):
        print collection

class ApplyMetadataTemplateVisitor(CollectionVisitor):
    def __init__(self, options):
        self.options = options
        
    def visit(self,  collection):
        template = None
        if self.options.extra_recursive:
            test = collection + "/" + DEFAULT_COLL_META_TEMPLATE
            logging.debug("Extra-recursive mode, looking for default template file '%s'." %  test)
            if iquest.dataobject_exists(test):
                template = test
                logging.info("Extra-recursive mode, using default template file '%s'." %  test)
            else:
                return
        
        else:
        # use user-provided a template file, if none given, look for default files.
            if self.options.template:
                template = self.options.template
            else:
                logging.info("Using default template file 'collectionMetadataTemplate'.")
                test = collection + "/" + DEFAULT_COLL_META_TEMPLATE
                if iquest.dataobject_exists(test):
                    template = test
            
            if not template:
                logging.error("No template object found.")
                return
                
# this check is useless, all Ida objects have metadata
#        if not iquest.dataobject_has_metadata(template):
#            logging.error("Template object " + template + " has no metadata.")
#            return

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
            if  tail != DEFAULT_COLL_META_TEMPLATE and target != template:
                if self.options.delete:
                    deleteMetadataFromDataObject(avus,  target,  self.options.dryrun)
                else:
                    addMetadata2DataObject(avus,  target,  self.options.dryrun)
                    
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
    
    # When the python script is started, it has own new shell, with a new irods environment
    # where the current working directory is ~. 
    # This command checks the current working directory of the parent shell from the .irodsEnv files.
    iutils.icd2ipwd()
    ipwd= iutils.ipwd()

    # check if template was given
    if not options.template:
        logging.info("No template given, using default (" + DEFAULT_COLL_META_TEMPLATE+ ").")
        options.template = DEFAULT_COLL_META_TEMPLATE

    # check if template is an absolute path
    if iquest.dataobject_exists(ipwd + "/" + options.template):
        options.template = ipwd + "/" + options.template
    else:
        if not iquest.dataobject_exists(options.template):
            parser.error("Template " + options.template + " not found.")
    logging.info("Using template " + options.template)

    # check if target is an absolute path (file or folder)
    # start with assumption that user gave path relative to ipwd
    TARGET_IS_A_SINGLE_FILE = False
    if options.target:
        if iquest.collection_exists(ipwd + "/" + options.target):
            options.target = ipwd + "/" + options.target
        elif iquest.collection_exists(options.target):
            True
        elif iquest.dataobject_exists(ipwd + "/" + options.target):
            TARGET_IS_A_SINGLE_FILE = True
            options.target = ipwd + "/" + options.target
        elif iquest.dataobject_exists(options.target):
            TARGET_IS_A_SINGLE_FILE = True
        else:
            parser.error("Target " + options.target + " not found")
        
        logging.info("Applying to target " + options.target)

    # if no target collection given, use the current iRODS working directory
    else:
        logging.info("Using current iRODS working directory (" + ipwd + ") as target.")
        options.target = ipwd

    if options.template == options.target:
        parser.error("Template and target are same.")

    if TARGET_IS_A_SINGLE_FILE:
        # get avus of the template object
        avus = iquest.get_metadata(options.template)
        if options.delete:
            deleteMetadataFromDataObject(avus,  options.target,  options.dryrun)
        else:
            addMetadata2DataObject(avus,  options.target,  options.dryrun)
        sys.exit(0)

    visitor = ApplyMetadataTemplateVisitor(options)
    #visitor = CollectionVisitor()
    if options.extra_recursive:
        options.recursive = True
        Walk(options.target,  visitor)
    else:
        visitor.visit(options.target)
    

if __name__ == "__main__":
    main()


    
