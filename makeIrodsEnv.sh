idauser=$1

mkdir .irods
chmod go-rx .irods
sed "s/IDA_USER_NAME/$idauser/" < /opt/LMU/irods-scripts/irodsEnvTemplate > .irods/.irodsEnv

