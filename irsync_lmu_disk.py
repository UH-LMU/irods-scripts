#!/usr/bin/env python
import datetime
import os
import sys
import smtplib
from email.mime.text import MIMEText
import time
import xml.etree.ElementTree as ET

config = sys.argv[1]
tree = ET.parse(config)
root = tree.getroot()

logroot = sys.argv[2]

for sync in root:
    user = sync.get("user")
    src = sync.get("src")
    dst = sync.get("dst")
    email = sync.get("email")

    t = time.time()
    ft = datetime.datetime.fromtimestamp(t).strftime('%Y%m%d-%H%M%S')

    log = logroot + "/irsync_" + ft + "_" + user + ".log"

    cmd = "irsync -VKr %s %s >& %s" % (src,dst,log)
    print cmd

    # run command
    os.system(cmd)

    # mail log to user
    fp = open(log, 'rb')
    # Create a text/plain message
    msg = MIMEText(fp.read())
    fp.close()

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = 'Ida transfer %s' % log
    msg['From'] = 'lmu-storage@helsinki.fi'
    msg['To'] = email

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(me, [you], msg.as_string())
    s.quit()
    
