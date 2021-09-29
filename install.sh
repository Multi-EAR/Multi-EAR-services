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
# Message to display for usage and help.
#
function usage
{
    local txt=(
"Multi-EAR $SCRIPT on a deployed Raspberry Pi OS LITE (32-bit)."
"Usage: $SCRIPT [options] <install_step>"
""
"Install step:"
"  all            Perform full deployment of all following steps (default)."
"  install        Install required packages."
"  config         Configure required packages."
"  python         Python3 virtual environment."
"  services       Multi-EAR services."
""
"Options:"
"  --help, -h     Print help."
"  --version, -v  Print version."
    )

    printf "%s\n" "${txt[@]}"
    exit 0
}


#
# Message to display when bad usage.
#
function badUsage
{
    local message="$1"
    local txt=(
"For an overview of the command, execute:"
"$SCRIPT --help"
    )

    [[ $message ]] && printf "$message\n"

    printf "%s\n" "${txt[@]}"
    exit -1
}


#
# Message to display for version.
#
function version
{
    local txt=(
"$SCRIPT v$VERSION"
    )

    printf "%s\n" "${txt[@]}"
    exit 0
}


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
# Rsync etc and var
#
function rsync_etc_var
{
    echo ".. rsync /etc" | tee -a $LOG_FILE
    sudo rsync -amv --chown=root:root etc /etc >> $LOG_FILE 2>&1
    sudo mkdir -p /var/log/multi-ear >> $LOG_FILE 2>&1
    sudo chown -r $USER:$USER /var/log/multi-ear >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


#
# Installs
#
function install_python3
{
    echo ".. install python3" | tee -a $LOG_FILE
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y libatlas-base-dev >> $LOG_FILE 2>&1
    sudo apt install -y python3 python3-pip python3-venv >> $LOG_FILE 2>&1
    sudo apt install -y python3-numpy python3-gpiozero python3-serial >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1

    echo ".. set pip trusted hosts and self update" | tee -a $LOG_FILE
    cat <<EOF | sudo tee /etc/pip.conf
[global]
extra-index-url=https://www.piwheels.org/simple
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
EOF
    python3 -m pip install --upgrade pip >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function install_nginx
{
    echo ".. install nginx" | tee -a $LOG_FILE
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y nginx >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function install_hostapd_dnsmasq
{
    echo ".. install hostapd dnsmasq" | tee -a $LOG_FILE
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y hostapd dnsmasq >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function install_influxdb_telegraf
{
    echo ".. install influxdb" | tee -a $LOG_FILE
    # add to apt
    wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add - >> $LOG_FILE 2>&1
    echo "deb https://repos.influxdata.com/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list >> $LOG_FILE 2>&1
    # install
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y influxdb telegraf >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function install_grafana
{
    echo ".. apt install grafana" | tee -a $LOG_FILE
    # add to apt
    curl https://packages.grafana.com/gpg.key | sudo apt-key add - >> $LOG_FILE 2>&1
    echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list >> $LOG_FILE 2>&1
    # install
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y grafana >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function installs
{
    install_python3
    install_nginx
    install_hostapd_dnsmasq
    install_influxdb_telegraf
    install_grafana
}


#
# Python3 virtual environment
#
function create_python3_venv
{
    echo ".. create python3 venv in $VIRTUAL_ENV" | tee -a $LOG_FILE
    sudo mkdir $VIRTUAL_ENV >> $LOG_FILE 2>&1
    sudo chown -R $USER:$USER $VIRTUAL_ENV >> $LOG_FILE 2>&1
    python3 -m venv $VIRTUAL_ENV >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


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
# Configures
#
function configure_python3
{
    create_python3_venv
    activate_python3_venv
}


function configure_nginx
{
    echo ".. configure influxdb" | tee -a $LOG_FILE
    # remove default nginx site
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo rm -f /etc/nginx/sites-available/default
    # test
    sudo service nginx configtest
    # enable and start service
    sudo systemctl unmask nginx >> $LOG_FILE 2>&1
    sudo systemctl enable nginx >> $LOG_FILE 2>&1
    sudo systemctl start nginx >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function configure_hostapd_dnsmasq
{
    echo ".. configure hostapd dnsmasq" | tee -a $LOG_FILE
    sudo systemctl stop hostapd >> $LOG_FILE 2>&1
    sudo systemctl stop dnsmasq >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function configure_influxdb
{
    echo ".. configure influxdb" | tee -a $LOG_FILE
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


function configure_telegraf
{
    echo ".. configure telegraf" | tee -a $LOG_FILE
    # enable and start service
    sudo systemctl unmask telegraf >> $LOG_FILE 2>&1
    sudo systemctl enable telegraf >> $LOG_FILE 2>&1
    sudo systemctl start telegraf >> $LOG_FILE 2>&1
    # configure
    sudo cp etc/telegraf/telegraf.conf /etc/telegraf/telegraf.conf >> $LOG_FILE 2>&1
    # restart service
    sudo systemctl start telegraf >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1

    # configure, enable service, create database
}


function configure_grafana
{
    echo ".. configure grafana" | tee -a $LOG_FILE
    # plugins 
    sudo grafana-cli plugins install grafana-clock-panel
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


function configures
{
    configure_python3
    configure_nginx
    configure_hostapd_dnsmasq
    configure_influxdb
    configure_telegraf
    configure_grafana
}


#
# Multi-EAR services
#
function multi_ear_services
{
    echo ".. setup multi-ear systemd services" | tee -a $LOG
    services=$(ls etc/system.d/system/multi-ear-*.service)

    sudo systemctl daemon-reload >> $LOG_FILE 2>&1
    for service in $services
    do
        # apply per multi-ear-service
        echo ".. setup systemd $service" >> $LOG_FILE 2>&1
        sudo systemctl stop $service >> $LOG_FILE 2>&1
        sudo systemctl enable $service >> $LOG_FILE 2>&1
        sudo systemctl start $service >> $LOG_FILE 2>&1
        echo -e ".. done\n" >> $LOG_FILE 2>&1
    done

}


#
# Process options
#
while (( $# ));
do
    case "$1" in
        --help | -h) usage
        ;;
        --version | -v) version
        ;;
        *) break
    esac
    shift
done


# Perform one step or the entire workflow
case "${1}" in
    ""|all)
    rm -f $LOG_FILE
    echo "Multi-EAR Software Install Tool v${VERSION}" | tee $LOG_FILE
    installs
    rsync_etc_var
    configures
    multi_ear_services
    echo "Multi-EAR software install completed" | tee -a $LOG_FILE
    ;;
    i|install) installs
    ;;
    e|etc) rsync_etc_var
    ;;
    c|conf|config|configure) configures
    ;;
    s|serv|services) multi_ear_services
    ;;
    *) badUsage "Unknown command ${1}." | tee $LOG_FILE
    ;;
esac

exit 0
