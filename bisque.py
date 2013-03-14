import base64
import httplib2
import logging
import os.path
import urllib
import urllib2
import xml.etree.ElementTree as ET
#from xml.etree.ElementTree import Element,  SubElement

import imeta
from imeta import AVU
import iquest
import iutils

from applyCollectionMetadataTemplates import ATTRIBUTES_SET_BY_IDA

http = httplib2.Http(ca_certs="lmu-bisque1_nginx.pem")
logger = logging.getLogger(__name__)

ATTR_BISQUE_TEMPLATE = "bisque."
ATTR_BISQUE_URI = "bisque.uri"
ATTR_BISQUE_RESOURCE_UNIQ = "bisque.resource_uniq"    
BISQUE_ADD_IMAGE = "/import/insert_inplace"
BISQUE_DATASET = "/data_service/dataset/"

SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif", ".ids", ".ics", ".sld"]

def is_image(filename):
    file,  ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext in SUPPORTED_FORMATS:
        return True
    return False
    
def _avus2tags(avus):
    resource = ET.Element("resource")
    for avu in avus:
        if not avu.a.startswith(ATTR_BISQUE_TEMPLATE) and avu.a not in ATTRIBUTES_SET_BY_IDA:
            tag = ET.SubElement(resource,"tag")
            tag.set("name", avu.a)
            tag.set("value", avu.v)

    return ET.tostring(resource)

def _create_resource(name,  value):
    resource = ET.Element("resource")
    resource.set("name",  name)
    resource.set("value",  value)
    return resource

def _add_tags(resource,  avus):
    for avu in avus:
        if not avu.a.startswith(ATTR_BISQUE_TEMPLATE) and avu.a not in ATTRIBUTES_SET_BY_IDA:
            tag = ET.SubElement(resource,"tag")
            tag.set("name", avu.a)
            tag.set("value", avu.v)

    
class BisqueConnection:

    def __init__(self,  bisque_host,  username,  password):
        self.bisque_host = bisque_host
        self.bisque_user = username
        self.bisque_pass = password
        #self.auth = {'authorization' : 'Basic '+base64.encodestring("%s:%s" % (username,password)).strip()}

        
    def register_irods_file(self,  irods_host, irods_file,  dryrun=False):
        irods_url = irods_host + irods_file
        bisque_url = self.bisque_host + BISQUE_ADD_IMAGE
        
        if is_image (irods_file ):
            logger.debug("Registering " + irods_url)

            # send also iRODS metadata
            avus = iquest.get_metadata(irods_file)
            tags = _avus2tags(avus)
            logger.debug("Tags: \n" + tags)
            #bisque_url += "?" + urllib.urlencode( { 'url': irods_url, 'tags': tags})
            logging.info( "POSTING " + bisque_url)
            
            request = urllib2.Request(bisque_url)
            request.add_header("authorization", 'Basic '+base64.encodestring("%s:%s" % (self.bisque_user,self.bisque_pass)).strip())
            #resource = "<resource name='%s' value='%s'/>" % (os.path.basename(irods_url),  irods_url)
            resource = _create_resource(os.path.basename(irods_url),  irods_url)
            _add_tags(resource,  avus)
            logger.debug("resource with tags\n" + ET.tostring(resource))
            resource =  urllib.urlencode({"user" : self.bisque_user,  "irods_resource" : ET.tostring(resource)})
            request.add_data(resource)

            if not dryrun:
                try:
                    
                    opener = urllib2.build_opener(
                                                  urllib2.HTTPRedirectHandler(), 
                                                  urllib2.HTTPHandler(debuglevel=0), 
                                                  urllib2.HTTPSHandler(debuglevel=0))
                    r = opener.open(request)
                    response = r.read()
                    logger.debug(response)
                except Exception,  e:
                    logger.error("Caught exception %s" % e)
                    raise e

                # read Bisque attributes from reply
                resource = ET.fromstring(response)
                image = resource.find("image")
                resource_uniq = image.get("resource_uniq")
                uri = image.get("uri")
                logger.debug(resource_uniq)
                logger.debug(uri)
                # store Bisque attributes in iRODS metadata
                if iquest.dataobject_has_attribute(irods_file,  ATTR_BISQUE_URI):
                    logging.warning("File '" + irods_file + "' was already registered in Bisque.")
                    imeta.delete(irods_file, AVU(ATTR_BISQUE_URI,"", ""))
                    imeta.delete(irods_file, AVU(ATTR_BISQUE_RESOURCE_UNIQ,"", ""))
                imeta.add(irods_file, AVU(ATTR_BISQUE_URI,  uri))
                imeta.add(irods_file, AVU(ATTR_BISQUE_RESOURCE_UNIQ,  resource_uniq))

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
        dataset = ET.SubElement(resource, "dataset")
        for i in range(0, len(ids)):
            # get the bisque uri of the file
            uri = iquest.get_attribute(ids[i])
            if not uri.startswith("http"):
                logger.warning("Invalid Bisque URI " + uri)
                continue
            value = ET.SubElement(dataset,"value")
            value.set("index",  str(i))
            value.set("type", "object")
            value.text = uri
        logger.debug(resource.tostring())
        
        
