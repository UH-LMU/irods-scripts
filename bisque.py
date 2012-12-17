import base64
import httplib2
import logging
import os.path
import urllib
import xml.etree.ElementTree as ET

import imeta
from imeta import AVU
import iquest
import iutils

http = httplib2.Http()
logger = logging.getLogger(__name__)

ATTR_BISQUE_TEMPLATE = "bisque."
ATTR_BISQUE_URI = "bisque.uri"
ATTR_BISQUE_RESOURCE_UNIQ = "bisque.resource_uniq"    
BISQUE_ADD_IMAGE = "/import/insert/"
BISQUE_DATASET = "/data_service/dataset/"

SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif"]

def is_image(filename):
    file,  ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext in SUPPORTED_FORMATS:
        return True
    return False

def _avus2tags(avus):
    tags = "<resource>"
    for avu in avus:
        if not avu.a.startswith(ATTR_BISQUE_TEMPLATE):
            tag = '<tag name=\"%s\" value=\"%s\"/>' % (avu.a, avu.v)
            tags += tag
            tags += '</resource>'
    return tags
    

class BisqueConnection:

    def __init__(self,  bisque_host,  username,  password):
        self.bisque_host = bisque_host
        self.auth = {'authorization' : 'Basic '+base64.encodestring("%s:%s" % (username,password)).strip()}

        
    def register_irods_file(self,  irods_host, irods_file,  dryrun=False):
        irods_url = irods_host + irods_file
        bisque_url = self.bisque_host + BISQUE_ADD_IMAGE
        
        if is_image (irods_file ):
            logger.debug("Registering " + irods_url)

            # send also iRODS metadata
            avus = iquest.get_metadata(irods_file)
            tags = _avus2tags(avus)
            #bisque_url += '?url=' + irods_url
            #bisque_url += '?url=' + irods_url
            bisque_url += "?" + urllib.urlencode( { 'url': irods_url, 'tags': tags})
            logging.info( "POSTING " + bisque_url)
            if not dryrun:
                resp,  content = http.request(bisque_url, headers = self.auth)
                logger.debug(content)
                # read Bisque attributes from reply
                image = ET.fromstring(content)
                resource_uniq = image.get("resource_uniq")
                uri = image.get("uri")
                logger.debug(resource_uniq)
                logger.debug(uri)
                # store Bisque attributes in iRODS metadata
                if iquest.dataobject_has_attribute(irods_file,  ATTR_BISQUE_URI):
                    logging.warning("File '" + irods_file + "' was already registered in Bisque.")
                    imeta.delete(irods_file, [AVU(ATTR_BISQUE_URI,"", ""), AVU(ATTR_BISQUE_RESOURCE_UNIQ,"", "")])
                imeta.add(irods_file, ATTR_BISQUE_URI,  uri)
                imeta.add(irods_file, ATTR_BISQUE_RESOURCE_UNIQ,  resource_uniq)

        else:
            logger.info("Unsupported file format, skipping " + irods_url)
        

    def register_irods_avus(self,  irods_file,  bisque_uri=None, dryrun=False):
        avus = iquest.get_metadata(irods_file)
        # find bisque uri if nto given
        if not bisque_uri:
            bisque_uri = avus[ATTR_BISQUE_URI]
            if not bisque_uri:
                logger.error("Metadata attribute '" + ATTR_BISQUE_URI + "' not set. Register the dataobject to Bisque first.")
                return
                
    def create_dataset(self, name):
        # Dataset in irods is defined by AVU 'dataset=name'. Find all matching files.
        ids = iquest.get_dataids_dataset(name)
        if len(files) == 0:
            logger.error("Dataset is empty.")
            return
            
        irods_host = iutils.ihost()
        
        # prepare xml document describing the dataset
        resource = ET.Element("resource")
        dataset = resource.SubElement("dataset")
        for i in range(0, len(ids)):
            # get the bisque uri of the file
            uri = iquest.get_attribute(ids[i])
            if not uri.startswith("http"):
                logger.warning("Invalid Bisque URI " + uri)
                continue
            value = dataset.SubElement("value")
            value.set("index",  str(i))
            value.set("type", "object")
            value.text = uri
        logger.debug(resource.tostring())
        
        
