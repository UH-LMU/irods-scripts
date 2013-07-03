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

Create a file in iRODS and add standard metadata fields.  This file can subsequently be used as metadata template.
Run '%prog -h' for options.
"""

# Required Ida metadata attributes (http://www.csc.fi/sivut/ida/ohjeet/kayttoohjeet/Kuvailuvaatimus)
ATTR_TITLE = "Title"
ATTR_TITLE_LANG = "Title.lang"
ATTR_RIGHTS_CATEGORY = "Rights.category"
ATTR_RIGHTS_DECLARATION = "Rights.declaration"
ATTR_SUBJECT = "Subject"
ATTR_CREATOR = "Creator"
ATTR_OWNER = "Owner"
ATTR_LANGUAGE = "Language"

# LMU metadata
ATTR_PI = "Research group"
ATTR_PROJECT = "Project"
ATTR_DATASET = "Dataset"
ATTR_ORGANISM = "Organism"
ATTR_INSTRUMENT = "Instrument"
ATTR_METHOD = "Method"
ATTR_LIVE = "Live"
ATTR_FIXED = "Fixed"
ATTR_SCREENING = "Screening"

# file used to store collection metadata
DEFAULT_COLL_META_TEMPLATE = "collectionMetadataTemplate"

DEFAULT_RIGHTS_CATEGORY= ""
DEFAULT_RIGHTS_DECLARATION= ""

def main():
    parser = OptionParser(usage=usage)
    parser.add_option('--title',  help='Concise description of the subject matter.')
    parser.add_option('-b', '--title-lang',  default='eng',  help='Title language.')
    parser.add_option('-r', '--rights-category', default=DEFAULT_RIGHTS_CATEGORY, help="")
    parser.add_option('-R', '--rights-declaration', default=DEFAULT_RIGHTS_DECLARATION, help="")
    parser.add_option('-s', '--subject', default=False, help="Comma separated list of terms describing the subject.")
    parser.add_option('-c', '--creator', default=False, help="")
    parser.add_option('-o', '--owner', default=False, help="")
    parser.add_option('-l', '--language', default='-', help="")

    options, args = parser.parse_args()

    template = DEFAULT_COLL_META_TEMPLATE
    if len(args) > 0:
        template = args[0]
    print template
    

    

if __name__ == "__main__":
    main()

