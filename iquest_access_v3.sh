#!/bin/bash

#
# Authors: Taneli Riitaoja, CSC
#          Harri Jäälinoja, LMU
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

debug "coll_users"
while read line
do
    user_name=`echo "$line" | awk -F"###" '{ print $1 }'`
    user_id=`echo "$line" | awk -F "###" '{ print $2 }'`
    debug $user_name
    if [[ "$user_name" == *.* ]]
    then
        users=`igroupadmin lg "$user_name" | grep "#" | awk -F "#" '{ print $1 }'`
        groupusers=""
        while read guser
        do
            guser_id=`iquest --no-page "%s" "SELECT USER_ID WHERE USER_NAME = '$guser'"`
            if [[ -z "${user_name_id_map["$guser_id"]}" ]]
            then
                user_name_id_map+=( ["$guser_id"]="$guser" )
            fi
            groupusers+="&&&$guser"
        done <<< "$users"
        groups+=("$user_id###$user_name%%%$groupusers")
    else
        user_name_id_map+=( ["$user_id"]="$user_name" )
    fi
done <<< "$coll_users"

debug "colls"
while read line
do
    debug $line

    group_own=()
    group_read=()
    group_write=()

    debug "Groups"
    for group in "${groups[@]}"
    do
        debug $group

        group_id=`echo "$group" | awk -F"###" '{ print $1 }'`
        group_name=`echo "$group" | awk -F"###" '{ print $2 }' | awk -F"%%%" '{ print $1 }'`
        group_users=`echo "$group" | awk -F"###" '{ print $2 }' | awk -F"%%%" '{ print $2 }'`
        IFS='&&&' read -r -a users <<< "$group_users"
        coll_access_info=`iquest --no-page "%s###%s" "SELECT COLL_ACCESS_USER_ID, COLL_ACCESS_NAME WHERE COLL_NAME = '${line}' AND COLL_ACCESS_USER_ID = '${group_id}'" 2> /dev/null`
        if [[ -z "$coll_access_info" ]]
        then
            continue
        fi

        access_name=`echo "$coll_access_info" | awk -F"###" '{ print $2 }'`
        for guser in "${users[@]}"
        do
            if [[ -z "$guser" ]]
            then
                continue
            fi
            if [[ "$access_name" == "own" ]]
            then
                group_own+=( "$guser" )
            elif [[ "$access_name" == "read" ]]
            then
                group_read+=( "$guser" )
            elif [[ "$access_name" == "write" ]]
            then
                group_write+=( "$guser" )
            fi
        done
    done

    debug "Users"
    coll_access_string=""
    readable_by_lmu="true"
    for uid in "${!user_name_id_map[@]}"
    do
        user_name="${user_name_id_map["$uid"]}"
        debug $user_name
        if [[ "$user_name" == "rods" ]] || [[ "$user_name" == "rodsadmin" ]]
        then
          debug "skipping $user_name"
          continue
        fi

        coll_access_info=`iquest --no-page "%s###%s" "SELECT COLL_ACCESS_USER_ID, COLL_ACCESS_NAME WHERE COLL_NAME = '${line}' AND COLL_ACCESS_USER_ID = '${uid}'" 2> /dev/null`
        if [[ "$?" != "0" ]] || [[ "$coll_access_info" == *"CAT"* ]]
        then
            if [[ " ${group_own[@]} " =~ " ${user_name} " ]]
            then
                access_name="own"
            elif [[ " ${group_read[@]} " =~ " ${user_name} " ]]
            then
                access_name="read"
            elif [[ " ${group_write[@]} " =~ " ${user_name} " ]]
            then
                access_name="write"
            else
                access_name="null"
            fi
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
      echo "Collection not readable by LMU: ${line}; permissions: ${coll_access_string}"
    fi
done <<< "$colls"
