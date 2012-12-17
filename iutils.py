import logging
import os
import os.path
import subprocess

logger = logging.getLogger(__name__)

def ienv():
    proc = subprocess.Popen('ienv', stdout=subprocess.PIPE)
    ienv  = {}
    lines = proc.stdout.readlines()
    for l in lines:
        l = l.rstrip()
        l = l.replace("NOTICE: ", "")
        if l.startswith("irods"):
            (key, value) = l.split("=")
            ienv[key] = value
    return ienv

def ihost():
    env = ienv()
    return env["irodsHost"]
    
def ipwd():
    proc = subprocess.Popen('ipwd', stdout=subprocess.PIPE)
    output = []
    lines = proc.stdout.readlines()
    return lines[0].rstrip()

#def icd2ipwd():
#    env = ienv()
#    ipwd = env["irodsCwd"]
#    
#    cmd = ["icd",  ipwd]
#    subprocess.call(cmd)


def sorted_ls(path):
    mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
    return list(sorted(os.listdir(path), key=mtime,  reverse=True))

def icd2ipwd():
    path = "~/.irods"
    path = os.path.expanduser(path)
    envfiles = sorted_ls(path)
    
    # find the latest .irodsEnv file
    for e in envfiles:
        if e.startswith(".irodsEnv") != -1:
            currentEnv = e.rstrip()
            break
    
    currentEnv = path + "/" + currentEnv
    logger.debug(currentEnv)
    
    # find latest irods working directory
    file = open(currentEnv,  'r')
    lines = file.readlines()
    file.close()
    env = {}
    for l in lines:
        if l.startswith("irods"):
            (key, val) = l.split("=")
            env[key] =  val
    irodsCwd = env['irodsCwd'].rstrip()

    cmd = ["icd",  irodsCwd]
    subprocess.call(cmd)
