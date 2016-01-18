#!/bin/bash

#
# Author: Harri Jäälinoja, LMU
#

function debug() {
  true
  #echo "DEBUG: $1"
}

if [[ -z "$1" ]] || [[ -z "$2" ]]
then
    exit 1
fi

# we will check the permissions of data in this collection
colls=`iquest --no-page "%s" "SELECT COLL_NAME WHERE COLL_NAME LIKE '${1}%'"`

# the permissions of this collection are used to list the users
# who should have access to all data in the previous collection
coll_users=`iquest --no-page "%s###%s" "SELECT USER_NAME, USER_ID WHERE COLL_NAME = '${2}'"`

declare -A user_name_id_map

declare -a groups

# this loop fills in user_name_id_map
# the alternative would be to hard code current LMU staff usernames and ids.
debug "coll_users"
while read line
do
    user_name=`echo "$line" | awk -F"###" '{ print $1 }'`
    user_id=`echo "$line" | awk -F "###" '{ print $2 }'`
    debug $user_name
    if [[ "$user_name" == *.* ]] || [[ "$user_name" == "rods" ]] || [[ "$user_name" == "rodsadmin" ]]
    then
      debug "skipping $user_name"
      continue
    else
        user_name_id_map+=( ["$user_id"]="$user_name" )
    fi
done <<< "$coll_users"

# read the id of the LMU Ida project group
group_id=`iquest --no-page "%s" "SELECT USER_ID WHERE USER_NAME = 'hy.hy7004'"`


# this loop goes through all the target collections
# alert if LMU staff does not have read access to the collection
debug "colls"
while read line
do
    debug $line

    # check what access group hy.hy7004 has to the collection
    coll_access_info=`iquest --no-page "%s###%s" "SELECT COLL_ACCESS_USER_ID, COLL_ACCESS_NAME WHERE COLL_NAME = '${line}' AND COLL_ACCESS_USER_ID = '${group_id}'" 2> /dev/null`
    coll_access_string=""

    # this is the case when hy.hy7004 doesn't have access to the collection
    if [[ "$?" != "0" ]] || [[ "$coll_access_info" == *"CAT"* ]]
    then

      # check if LMU staff members have access
      readable_by_lmu="true"
      for uid in "${!user_name_id_map[@]}"
      do
          user_name="${user_name_id_map["$uid"]}"

          coll_access_info=`iquest --no-page "%s###%s" "SELECT COLL_ACCESS_USER_ID, COLL_ACCESS_NAME WHERE COLL_NAME = '${line}' AND COLL_ACCESS_USER_ID = '${uid}'" 2> /dev/null`
          if [[ "$?" != "0" ]] || [[ "$coll_access_info" == *"CAT"* ]]
          then
            readable_by_lmu="false"
            access_name="null"
          else
            access_name=`echo "$coll_access_info" | awk -F"###" '{ print $2 }'`
          fi

          debug "$user_name $access_name $coll_access_info"
          coll_access_string+="${user_name_id_map["$uid"]}:${access_name} "
          if [[ "$access_name" == "null" ]]
          then
            readable_by_lmu="false"
          fi
      done

      if [[ "$readable_by_lmu" == "false" ]]
      then
        echo "ALERT: ${line} not readable by LMU staff. Permissions: ${coll_access_string}"
      else
        echo "${line} LMU staff has access: ${coll_access_string}"
      fi

    else
      echo "${line} hy.hy7004 has access: ${coll_access_info}"
    fi
done <<< "$colls"
