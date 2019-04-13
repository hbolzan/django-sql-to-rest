#!/bin/sh

function db_exists() {
    FOUND=$(psql -U postgres -h db -lqt | cut -d \| -f 1 | grep -w $1)
    if [ -z $FOUND ]
    then
        EXISTS=0
    else
        EXISTS=1
    fi
}

function restore_db() {
    psql -U postgres -h db $1 < $2
}

db_exists $1
if [ $EXISTS -gt 0 ]
then
    echo "$1 exists"
else
    restore_db $1 $2
fi
