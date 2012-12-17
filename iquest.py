import logging
import os
import os.path
import subprocess

from imeta import AVU

logger = logging.getLogger(__name__)

def getIquestOutput(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    output = []
    lines = proc.stdout.readlines()
    for l in lines:
        # remove trailing newline
        l = l.rstrip()
        # remove "'s from beginning and end
        l = l[:-1]
        l = l[1:]
        output.append(l)
    
    return output

def list_dataobjects(collection):
    cmd = ["iquest", "--no-page", "\"%s/%s\"", "\"select COLL_NAME,DATA_NAME where COLL_NAME = '" + collection + "'\""]
    logger.debug( " ".join(cmd))

    return getIquestOutput(cmd)

def list_dataobjects_recursive(collection):
    cmd = ["iquest", "--no-page", "\"%s/%s\"", "\"select COLL_NAME,DATA_NAME where COLL_NAME like '" + collection + "%'\""]
    logger.debug( " ".join(cmd))

    return getIquestOutput(cmd)

def list_child_collections(collection):
    cmd = ["iquest", "--no-page", "\"%s\"", "\"select COLL_NAME where COLL_PARENT_NAME = '" + collection + "'\""]
    logger.debug( " ".join(cmd))

    return getIquestOutput(cmd)

def collection_exists(coll):
    cmd = ["iquest",  "\"%s\"",  "\"select count(COLL_ID) where COLL_NAME = '"+ coll + "'\""]
    logger.debug( " ".join(cmd))
        
    out = getIquestOutput(cmd)
    out = int(out[0])
    if out > 0:
        return True
    else:
        return False
    
def dataobject_exists(dataobject):
    (head, tail) = os.path.split(dataobject)
    cmd = ["iquest",  "\"%s\"",  "\"select count(DATA_ID) where COLL_NAME = '"+ head + "' and DATA_NAME = '" + tail + "'\""]
    logger.debug( " ".join(cmd))
        
    out = getIquestOutput(cmd)
    out = int(out[0])
    if out > 0:
        return True
    else:
        return False
    
def child_collections_exist(collection):
    cmd = ["iquest",  "\"%s\"",  "\"select count(COLL_ID) where COLL_PARENT_NAME = '"+ collection + "'\""]
    logger.debug( " ".join(cmd))
        
    out = getIquestOutput(cmd)
    out = int(out[0])
    if out > 0:
        return True
    else:
        return False
    
def dataobject_has_metadata(dataobject):
    (head, tail) = os.path.split(dataobject)
    cmd = ["iquest",  "\"%s\"",  "\"select count(META_DATA_ATTR_NAME) where COLL_NAME = '" + head + "' and DATA_NAME = '" + tail + "'\""]
    logger.debug( " ".join(cmd))
        
    out = getIquestOutput(cmd)
    out = int(out[0])
    if out > 0:
        return True
    else:
        return False
    
def dataobject_has_attribute(dataobject,  attr):
    (head, tail) = os.path.split(dataobject)
    cmd = ["iquest",  "\"%s\"",  "\"select count(META_DATA_ATTR_NAME) where COLL_NAME = '" + head + "' and DATA_NAME = '" + tail + "' and META_DATA_ATTR_NAME = '" + attr +"'\""]
    logger.debug( " ".join(cmd))
        
    out = getIquestOutput(cmd)
    out = int(out[0])
    if out > 0:
        return True
    else:
        return False
    
def dataobject_get_attribute(dataid,  attr):
    cmd = ["iquest",  "\"%s\"",  "\"select META_DATA_ATTR_VALUE where DATA_ID = '" + dataid + "'\""]
    logger.debug( " ".join(cmd))
        
    out = getIquestOutput(cmd)
    return out[0]
    
def get_metadata(dataobject):
    (head, tail) = os.path.split(dataobject)
    cmd = ["iquest",  "\"%s####%s####%s\"",  "select META_DATA_ATTR_NAME, META_DATA_ATTR_VALUE, META_DATA_ATTR_UNITS where COLL_NAME = '"+ head + "' and DATA_NAME = '" + tail + "'\""]
    logger.debug( " ".join(cmd))

    out = getIquestOutput(cmd)
    avus = []
    for o in out:
        (a, v, u) = o.split("####")
        avus.append(AVU(a, v, u))
    return avus

def get_dataids_dataset(name):
    cmd = ["iquest",  "\"%s####%s####%s\"",  "select DATA_ID where META_DATA_ATTR_NAME = 'dataset' and META_DATA_ATTR_VALUE = '" + name + "'\""]
    logger.debug( " ".join(cmd))
    return getIquestOutput(cmd)
