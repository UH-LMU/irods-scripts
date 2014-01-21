#!/usr/bin/env python
import datetime
import os
import sys
import smtplib
from email.mime.text import MIMEText
from optparse import OptionParser
import re
import time
import xml.etree.ElementTree as ET

# regexps for checking the log
re_notice = re.compile("^NOTICE.*")
re_folder = re.compile("^C.*:$")
re_synced = re.compile("a match, no sync required")

def notify(sender,recipient,log):
    # mail log to user
    fp = open(log, 'rb')
    lines = fp.readlines()
    fp.close()

    # 7 lines means nothing happened
    if len(lines) > 7:
        # read the log lines to see if something was transferred
        transfers = 0
        for l in lines:
            if not (re.match(re_notice,l) or re.match(re_folder,l) or re.search(re_synced,l)):
                print l
                transfers = transfers + 1

        if transfers == 0:
            msg = MIMEText("All files have been uploaded to Ida. You can now remove them from LMU disk.")
            msg['Subject'] = 'Ida transfer complete'

        else:
            # Create a text/plain message
            msg = MIMEText("".join(lines))
            msg['Subject'] = 'Ida transfer %s' % log

        msg['From'] = sender
        msg['To'] = recipient
        
        print recipient

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP('localhost')
        s.sendmail(sender, [recipient], msg.as_string())
        s.quit()


def main():
    parser = OptionParser()
    parser.add_option('-u', '--user')
    
    options, args = parser.parse_args()
    config = args[0]
    print "config:",  config
    tree = ET.parse(config)
    root = tree.getroot()
    
    irsync = args[1]
    print "irsync:",  irsync
    logroot = args[2]
    print "logroot:",  logroot
    me = args[3]
    print "me:",  me

    for sync in root:
        user = sync.get("user")
        iuser = sync.get("iuser")
        src = sync.get("src")
        dst = sync.get("dst")
        email = sync.get("email")
        
        # if user was specified, process only that user
        if options.user and options.user != user:
            continue
    
        t = time.time()
        ft = datetime.datetime.fromtimestamp(t).strftime('%Y%m%d-%H%M%S')
    
        log = logroot + "/irsync_" + ft + "_" + user + ".log"
        cmd = "su -c \"%s -VKr %s %s >& %s\" -l %s" % (irsync,src,dst,log,user)
#        cmd = "echo \"%s -VKr %s %s >& %s\" -l %s" % (irsync,src,dst,log,user)

        cmd = cmd.encode("utf-8")
        print cmd
    
        # run command
        os.system(cmd)
    
        notify(me,email,log)

    
if __name__ == "__main__":
    main()
