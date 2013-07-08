#!/usr/bin/env python
import datetime
import os
import os.path
import re
import sys
import smtplib
from email.mime.text import MIMEText
import time
import xml.etree.ElementTree as ET

config = '/opt/LMU/irsync_config.xml'
logroot = '/var/log/LMU/iget_from_ida'
me = 'lmu-storage@helsinki.fi'

# taskfile names are of the form download_DATE_USER.sh
taskfile = sys.argv[1]
result = re.search('_([a-z,A-Z]*).sh', taskfile)
user = result.group(1)
print 'User: ', user

# subject of email sent to user
subject = sys.argv[2]

# find user's email from config file
email = me 
tree = ET.parse(config)
root = tree.getroot()
for irsync in root.findall('irsync'):
    #print irsync.attrib
    if irsync.get('user') == user:
        email = irsync.get('email')
print 'Email: ' + email

# log file name
head,tail = os.path.split(taskfile)
log = logroot + "/" + tail.replace('.sh','.log')

# run command
cmd = "%s >> %s 2>&1" % (taskfile,log)
print 'Command: ', cmd
print
logfile = open(log,'w')
print >> logfile, cmd
print >> logfile
print >> logfile, 'Downloading to LMU2/FROM_IDA/' + user + ':'
print >> logfile
logfile.close()
os.system(cmd)

# mail log to user
fp = open(log, 'rb')
# Create a text/plain message
msg = MIMEText(fp.read())
fp.close()

msg['Subject'] = subject
msg['From'] = me
msg['To'] = email

# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP('localhost')
s.sendmail(me, [email], msg.as_string())
s.quit()
    
