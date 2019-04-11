#!/bin/bash

# prepare a new server and deploy app
# assuming installation on an Ubuntu 18.04 box

# after launching a new server instance, follow these steps

# 1. send this script to server (you can use send-to-server.sh)
# 2. run new_sudo_user <username>
# 3. run install_docker
# 4. log off the server and log in again with the new sudo user you just created
# 5. run install_composer to install docker composer


export SELF=$0

set -a

### new_sudo_user
###   creates new user and adds to sudoers
###   must be root
###   usage:
###     $ new_sudo_user username
### 
function new_sudo_user() {
    USER_FOLDER=/home/$1
    USER_SSH_FOLDER=$USER_FOLDER/.ssh
    adduser $1
    usermod -aG sudo $1
    mkdir -p $USER_SSH_FOLDER
    cp /root/.ssh/authorized_keys $USER_SSH_FOLDER/.
    cp $SELF $USER_FOLDER/.
    chown $1. $USER_SSH_FOLDER/authorized_keys
    echo "###############"
    echo "You will be logged in as $1"
    echo "Now you should run the console script and install docker"
    echo "$ ./console.sh"
    echo "$ install_dcoker"
    echo "###############"
    echo ""
    su - $1
}

### install_docker
###   requires root permission to install docker
### 
function install_docker() {
    sudo apt install docker.io
    sudo usermod -aG docker $USER
    echo "User $USER was added to docker group"
    echo "You must log out this server and log in again"
}

### install_pip
###   installs python
### 
function install_pip() {
    sudo apt install -y python-pip
    echo "Python pip installed"
}

### install_composer
###   installs docker composer and all it's dependencies
### 
function install_composer() {
    install_pip
    sudo apt install -y python-dev libffi-dev libssl-dev gcc libc-dev make
    sudo curl -L \
         "https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$(uname -s)-$(uname -m)" \
         -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
}


### psql
###   logs into postgres container and runs psql as user postgres
###   usage:
###     $ psql <image-name> [database-name]
### 
function psql() {
    docker exec -it $1 psql -U postgres $2
}

### guide
###   shows this help
### 
function guide() {
    echo "Available functions"
    echo
    cat $SELF | grep -e "^###.*" | cut -d" " -f2-
}

function init() {
    echo "Prepare new server for deployment"
    guide
    bash
}

init
