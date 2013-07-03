#!/bin/bash
#
# chkconfig: 35 90 12
# description: ida-download-pyinotify
#
# Get function from functions library
. /etc/init.d/functions

CMD=/opt/LMU/irods-scripts/ida_download_pyinotify.py
LOG=/var/log/LMU/ida_download_pyinotify.log

# Start the script ida-download-pyinotify
start() {
        initlog -c "echo -n Starting ida-download-pyinotify: "
        daemon --user=hajaalin $CMD >& $LOG &
        ### Create the lock file ###
        touch /var/lock/subsys/ida-download-pyinotify
        success $"ida-download-pyinotify server startup"
        echo
}
# Restart the service ida-download-pyinotify
stop() {
        initlog -c "echo -n Stopping ida-download-pyinotify server: "
        killproc ida-download-pyinotify
        ### Now, delete the lock file ###
        rm -f /var/lock/subsys/ida-download-pyinotify
        echo
}
### main logic ###
case "$1" in
  start)
        start
        ;;
  stop)
        stop
        ;;
  status)
        status ida-download-pyinotify
        ;;
  restart|reload|condrestart)
        stop
        start
        ;;
  *)
        echo $"Usage: $0 {start|stop|restart|reload|status}"
        exit 1
esac
exit 0