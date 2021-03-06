#!/usr/bin/env python
import functools
import subprocess
import sys
import pyinotify

RUNCMDS = "/opt/LMU/irods-scripts/runcmds.py"

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_MOVED_TO(self, event):
        if event.name.startswith("download_"):
            cmd = [RUNCMDS,event.pathname,'Data downloaded to LMU2/FROM_IDA']
            print "Starting download task: ", cmd
            
            # start new process for the download task
            subprocess.Popen(cmd)

handler = EventHandler()
wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm, handler)
wm.add_watch('/var/log/LMU/ida_download_tasks', pyinotify.IN_MOVED_TO)

notifier.loop()
