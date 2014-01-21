SCRIPT=/opt/LMU/irods-scripts/irsync_lmu_disk.py
CONFIG=/opt/LMU/irsync_config_root.xml
IRSYNC=/opt/iRODS/iRODS_3.2/clients/icommands/bin/irsync 
LOGROOT=/var/log/LMU/irsync_to_ida 
EMAIL=lmu-storage@helsinki.fi
LOG=${LOGROOT}/irsync_lmu_disk_`date +%Y%m%d%H%M`.log

$SCRIPT $CONFIG $IRSYNC $LOGROOT $EMAIL >& $LOG

