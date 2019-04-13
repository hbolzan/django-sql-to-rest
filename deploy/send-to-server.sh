#!/bin/bash

# before running this script, your public key
# must be added to authorized keys on the server
# in DigitalOcean, this will be done durging droplet creation

# if the VS was just created and there is no ordinary user yet, run
# $ ./send-to-server hostname root
# to scp as root

if [ -z $2 ]
then
    echo "log in as $USER"
    LOGIN=$USER
else
    echo "log in as $2"
    LOGIN=$2
fi

scp console.sh $LOGIN@$1:~/.
