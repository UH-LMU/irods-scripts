#!/usr/bin/env python
import functools
import subprocess
import sys
import pyinotify

RUNCMDS = "/opt/LMU/irods-scripts/runcmds.py"

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_MOVED_TO(self, event):
        if event.name.startswith("download_"):
            cmd = [RUNCMDS,event.pathname]
            print "Starting download task: ", cmd
            
            # start new process for the download task
            subprocess.Popen(cmd)

handler = EventHandler()
wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm, handler)
wm.add_watch('/tmp/ida_downloads', pyinotify.IN_MOVED_TO)

notifier.loop()
