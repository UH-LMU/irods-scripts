#!/bin/bash

#
# Author: Taneli Riitaoja, CSC
#

if [[ -z "$1" ]] || [[ -z "$2" ]]
then
    exit 1
fi

colls=`iquest --no-page "%s" "SELECT COLL_NAME WHERE COLL_NAME LIKE '${1}%'"`

coll_users=`iquest --no-page "%s###%s" "SELECT USER_NAME, USER_ID WHERE COLL_NAME LIKE '${2}%'"`

declare -A user_name_id_map

declare -a groups

while read line
do
    user_name=`echo "$line" | awk -F"###" '{ print $1 }'`
    user_id=`echo "$line" | awk -F "###" '{ print $2 }'`
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

while read line
do
    group_own=()
    group_read=()
    group_write=()

    for group in "${groups[@]}"
    do

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

    coll_access_string=""
    for uid in "${!user_name_id_map[@]}"
    do
        user_name="${user_name_id_map["$uid"]}"
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
        #echo "DEBUG: $user_name $access_name $coll_access_info"
        coll_access_string+="${user_name_id_map["$uid"]}:${access_name} "
    done

    echo "${line}"
    echo "${coll_access_string}"
done <<< "$colls"
