#!/bin/bash

##############################################################################
# Script Name	: install.sh
# Description	: Automatic software installation for the Multi-EAR platform
#                 given a prepared install of RASPBERRY PI OS LITE (32-bit).
# Args          : n.a.
# Author       	: Pieter Smets
# Email         : mail@pietersmets.be
##############################################################################

# Current version
VERSION="0.1"

# Python virtual environment
VIRTUAL_ENV="/opt/py37"

# Log file
LOG_FILE="$(pwd)/install.log"

#
# Check if current user is tud
#
if [ $USER != "tud" ]; then
    echo "Script must be run as user: tud" | tee -a $LOG_FILE
    exit -1
fi

#
# Check for default user pi
#
if id -u pi >/dev/null 2>&1; then
    echo "Default user pi should not exit" | tee -a $LOG_FILE
    exit -1
fi

#
# Apt update
#
function apt_update
{
    echo ".. apt update" | tee -a $LOG_FILE
    sudo apt update >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}

#
# Apt upgrade
#
function apt_upgrade
{
    echo ".. apt upgrade" | tee -a $LOG_FILE
    sudo apt upgrade -y >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}

#
# Apt autoremove
#
function apt_autoremove
{
    echo ".. apt autoremove" | tee -a $LOG_FILE
    sudo apt autoremove -y >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}

#
# Apt sequence
#
function apt_sequence
{
    apt_update
    apt_upgrade
    apt_autoremove
}

#
# Install python3
#
function install_python3
{
    echo ".. apt install python3"
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y python3 python3-pip python3-venv >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1

    echo ".. set pip trusted hosts and self update"
    cat <<EOF | sudo tee -a /etc/pip.conf
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
EOF
    python3 -m pip install --upgrade pip >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}

#
# Install numpy and blas
#
function install_numpy_blas
{
    echo ".. apt install python3-numpy with BLAS support"
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y libatlas-base-dev >> $LOG_FILE 2>&1
    sudo apt install -y python3-numpy >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}

#
# Install influxdb
#
function install_influxdb
{
    echo ".. apt install influxdb"
    # add to apt
    wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add - >> $LOG_FILE 2>&1
    echo "deb https://repos.influxdata.com/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list >> $LOG_FILE 2>&1
    # install
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y influxdb >> $LOG_FILE 2>&1
    # enable and start service
    sudo systemctl unmask influxdb >> $LOG_FILE 2>&1
    sudo systemctl enable influxdb >> $LOG_FILE 2>&1
    sudo systemctl start influxdb >> $LOG_FILE 2>&1
    # configure
    sudo cp etc/influxdb/influxdb.conf /etc/influxdb/influxdb.conf >> $LOG_FILE 2>&1
    # restart service
    sudo systemctl start influxdb >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1

    # configure, enable service, create database
}

#
# Install grafana
#
function install_grafana
{
    echo ".. apt install grafana"
    # add to apt
    curl https://packages.grafana.com/gpg.key | sudo apt-key add - >> $LOG_FILE 2>&1
    echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list >> $LOG_FILE 2>&1
    # install
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y grafana >> $LOG_FILE 2>&1
    # enable and start service
    sudo systemctl unmask grafana >> $LOG_FILE 2>&1
    sudo systemctl enable grafana >> $LOG_FILE 2>&1
    sudo systemctl start grafana >> $LOG_FILE 2>&1
    # configure
    sudo cp etc/grafana/grafana.conf /etc/grafana/grafana.ini >> $LOG_FILE 2>&1
    # restart service
    sudo systemctl start grafana >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1

    # configure, enable service, link to database
}

#
# Create python3 virtual environment
#
function create_python3_venv
{
    echo ".. create python3 venv in $VIRTUAL_ENV" | tee -a $LOG_FILE
    sudo mkdir $VIRTUAL_ENV >> $LOG_FILE 2>&1
    sudo chown -R $USER:$USER $VIRTUAL_ENV >> $LOG_FILE 2>&1
    python3 -m venv $VIRTUAL_ENV >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}

#
# Activate python3 virtual environment
#
function activate_python3_venv
{
    echo ".. activate python3 venv" | tee -a $LOG_FILE
    if ! grep -q "source $VIRTUAL_ENV/bin/activate" "/home/$USER/.bashrc"; then
        echo "add source activate to .bashrc" >> $LOG_FILE 2>&1
        echo -e "\n# Multi-EAR python3 venv\nsource $VIRTUAL_ENV/bin/activate" | tee -a /home/$USER/.bashrc >> $LOG_FILE 2>&1
    else
        echo "source activate already exists in .bashrc" >> $LOG_FILE 2>&1
    fi
    source $VIRTUAL_ENV/bin/activate >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}

#
# Multi-EAR services
#
function install_services
{
    echo ".. setup services" | tee -a $LOG_FILE
    DIR="/opt/services"
    sudo mkdir $DIR >> $LOG_FILE 2>&1
    sudo chown -R $USER:$USER $DIR >> $LOG_FILE 2>&1

    echo ".... multi-ear-uart.service" | tee -a $LOG_FILE
    cd services/uart
    bash install.sh $VIRTUAL_ENV $LOG_FILE
    cd ../..

    echo ".... multi-ear-ctrl.service" | tee -a $LOG_FILE
    cd services/ctrl
    bash install.sh $VIRTUAL_ENV $LOG_FILE
    cd ../..
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}

#
# Setup sequence
#
echo "Multi-EAR software install v$VERSION" | tee $LOG_FILE
install_python3
install_numpy_blas
install_influxdb
install_grafana
create_python3_venv
activate_python3_venv
install_services
echo  "install complete" | tee -a $LOG_FILE

exit 0
