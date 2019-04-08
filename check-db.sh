#!/bin/sh

function check_db() {
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

check_db $1
if [ $EXISTS -gt 0 ]
then
        echo "$1 exists"
else
        restore_db $1 $2
fi
