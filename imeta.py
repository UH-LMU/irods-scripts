import logging
import subprocess

logger = logging.getLogger(__name__)

class AVU:
    def __init__(self, a, v, u=""):
        self.a = a
        self.v = v
        self.u = u
        
def run_cmd(cmd,  dryrun):
    logger.debug( " ".join(cmd))
    if not dryrun:
        subprocess.call(cmd)


def add(target, avu,  dryrun = False):
    cmd = ["imeta", "add", "-d",  target, avu.a, avu.v, avu.u]
    run_cmd(cmd,  dryrun)
    
def copy(template,  target,  dryrun = False):
    if template == target:
        return
        
    cmd = ["imeta", "cp", "-d", "-d",  template,  target]
    run_cmd(cmd,  dryrun)

def delete(target,  avu,  dryrun = False):
    cmd = ["imeta", "rmw", "-d",  target,  avu.a, "%"]
    run_cmd(cmd,  dryrun)

