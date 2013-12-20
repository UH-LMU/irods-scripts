#!/usr/bin/env python
import datetime
from optparse import OptionParser
import os
import os.path
import re
import time

from iquest import list_child_collections, get_file_count_and_data_size

LOGDIR = "/var/log/LMU/ida_usage/"
LOGDIRDAILY = LOGDIR + "daily/"
LOGDIRSUMMARY = LOGDIR + "summary/"

PROJECT = "/ida/hy/hy7004"
RESC_GROUP_NAMES = "'rg-1', 'rg-2', 'rg-3', 'rg-4', 'rg-9', 'rg-10'"
RESC_GROUP_NAMES = ""

t = time.time()
ft = datetime.datetime.fromtimestamp(t).strftime('%Y%m%d')

def log_raw():
    groups = list_child_collections(PROJECT)
    testgroups = ['/ida/hy/hy7004/Yliperttula', 'published', 'Jernvall']
    #groups = testgroups

    # LMU totals
    lmu_files = 0
    lmu_datasize = 0
    
    # This loop gets the usage today
    for g in groups:
        # group name
        head, group_name = os.path.split(g)
    
        # group totals
        group_files = 0
        group_datasize = 0
        
        # group members
        users = list_child_collections(g)
        for u in users:
            files, datasize = get_file_count_and_data_size(u, RESC_GROUP_NAMES)
            
            # update totals
            group_files = group_files + files
            group_datasize = group_datasize + datasize
            lmu_files = lmu_files + files
            lmu_datasize = lmu_datasize + datasize
            
            # write current usage
            head, name = os.path.split(u)
            filename = LOGDIRDAILY + "usage_" + group_name + "_" + name + "-" + ft + ".log"
            file = open(filename,  'w')
            print >> file, "# Ida usage of user '%s' on %s, file count and GB" % (u, ft)
            print >> file,  files,  datasize
            file.close()

        # write current group usage
        head, name = os.path.split(u)
        filename = LOGDIRDAILY + "usage_group_" + group_name + "-" + ft + ".log"
        file = open(filename,  'w')
        print >> file, "# Ida usage of '%s' on %s, file count and GB" % (g, ft)
        print >> file,  files,  datasize
        file.close()

    # write LMU total usage
    filename = LOGDIRDAILY + "usage_HY7004-" + ft + ".log"
    file = open(filename,  'w')
    print >> file, "# Ida usage of HY7004 on %s, file count and GB" % (ft)
    print >> file,  lmu_files,  lmu_datasize
    file.close()



# regexp to find user name and date
relog = re.compile("usage_(.*)-([0-9]*).log")

def read_daily_log(filename):
    file = open(LOGDIRDAILY+filename, 'r')
    lines = file.readlines()
    file.close()

    files,  gigas = lines[1].rstrip().split()
    return int(files),  int(gigas)


def log_summary():
    # list of log files, latest first
    logs = sorted(os.listdir(LOGDIRDAILY ), reverse=True)
    
    for i in range(0, len(logs)-1):
        user = None
        date = None
        res = relog.search(logs[i])
        if res:
            user = res.group(1)
            date = res.group(2)
            print user
        else:
            print "user not found in ",  logs[i]
        
        # check if there is a previous log or if this user was done already
        if logs[i+1].find(user) == -1 or logs[i-1].find(user) != -1:
            continue
            
        latest = logs[i]
        previous = logs[i+1]
        #print "find differences",  latest,  previous
        
        files_n,  gigas_n = read_daily_log(latest)
        files_p,  gigas_p = read_daily_log(previous)
        
        diff_files = files_n - files_p
        diff_gigas = gigas_n - gigas_p
    
        # write summary
        filename = LOGDIRSUMMARY + "summary_" + user + "-" + ft + ".log"
        file = open(filename,  'w')
        print >> file, "# Ida usage summary for '%s' on %s" % (user, ft)
        print >> file, "files_n, files_p,diff_files,data_GB_n,data_GB_p,diff_data_GB"
        print >> file,  "%d,%d,%d,%d,%d,%d" % (files_n, files_p, diff_files, gigas_n, gigas_p, diff_gigas)
        file.close()


if  __name__ =='__main__':
    parser = OptionParser(usage="")
    parser.add_option('-r', '--raw-only', action="store_true", default=False, help="only daily raw data")
    parser.add_option('-s', '--summary-only', action="store_true", default=False, help="only daily summary")

    options, args = parser.parse_args()
    if not options.summary_only:
        log_raw()
    if not options.raw_only:
        log_summary()
