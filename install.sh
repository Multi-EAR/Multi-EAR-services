#!/bin/bash

##############################################################################
# Script Name	: install.sh
# Description	: Automatic software installation for the Multi-EAR platform
#                 given a prepared install of RASPBERRY PI OS LITE (32-bit).
# Args          : n.a.
# Author       	: Pieter Smets
# Email         : mail@pietersmets.be
##############################################################################

# Name of the script
SCRIPT=$( basename "$0" )

# Current version from git
VERSION=$( git describe --tag --abbrev=0 2>&1 )

# Python virtual environment
VIRTUAL_ENV="/home/tud/.py37"

# Log file
LOG_FILE="$(pwd)/install.log"


#
# Check if device is a Raspberry Pi
#
function isRaspberryPi
{
    local pi=""
    if [ -f /proc/device-tree/model ];
    then
        pi=$( cat /proc/device-tree/model | tr '\0' '\n' | grep "Raspberry Pi" )
    fi
    if [ "x${pi}" == "x" ];
    then
        echo "Error: device is not a Raspberry Pi!"
        exit 1
    fi
}


#
# Message to display for usage and help.
#
function usage
{
    local txt=(
"Multi-EAR system services install on a deployed Raspberry Pi OS LITE (32-bit)."
"Usage: $SCRIPT [options] <install_step>"
""
"Install step:"
"  all            Perform all of the following steps (default)."
"  packages       Install all required packages via apt."
"  configure      Configure all packages (make sure /etc is synced)."
"  python         Create the Python3 virtual environment (py37)."
"  multi-ear      Install and enable the Multi-EAR software."
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
"$SCRIPT $VERSION"
    )

    printf "%s\n" "${txt[@]}"
    exit 0
}


#
# Installs
#
function do_install_libs
{
    echo ".. install libs" | tee -a $LOG_FILE
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y libatlas-base-dev >> $LOG_FILE 2>&1
    sudo apt install -y build-essential libssl-dev libffi-dev >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}

function do_install_python3
{
    echo ".. install python3" | tee -a $LOG_FILE
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y python3 python3-pip python3-dev python3-venv python3-setuptools >> $LOG_FILE 2>&1
    sudo apt install -y python3-numpy python3-gpiozero python3-serial >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
    echo ".. set pip trusted hosts" >> $LOG_FILE 2>&1
    cat <<EOF | sudo tee /etc/pip.conf >> $LOG_FILE 2>&1
[global]
extra-index-url=https://www.piwheels.org/simple
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
EOF
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_install_nginx
{
    echo ".. install nginx" | tee -a $LOG_FILE
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y nginx >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_install_hostapd
{
    echo ".. install hostapd" | tee -a $LOG_FILE
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y hostapd >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_install_dnsmasq
{
    echo ".. install dnsmasq" | tee -a $LOG_FILE
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y dnsmasq >> $LOG_FILE 2>&1
    sudo apt purge -y dns-root-data >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_install_influxdb_telegraf
{
    echo ".. install influxdb & telegraf" | tee -a $LOG_FILE
    # add to apt
    wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add - >> $LOG_FILE 2>&1
    echo "deb https://repos.influxdata.com/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list >> $LOG_FILE 2>&1
    # install
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y influxdb telegraf >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_install_grafana
{
    echo ".. install grafana" | tee -a $LOG_FILE
    # add to apt
    curl -s https://packages.grafana.com/gpg.key | sudo apt-key add - >> $LOG_FILE 2>&1
    echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list >> $LOG_FILE 2>&1
    # install
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y grafana >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_install
{
    do_install_libs
    do_install_python3
    do_install_nginx
    do_install_dnsmasq
    do_install_hostapd
    do_install_influxdb_telegraf
    do_install_grafana
}


#
# Python3 virtual environment
#
function do_create_python3_venv
{
    echo ".. create python3 venv in $VIRTUAL_ENV" | tee -a $LOG_FILE
    # check if already exists
    if [[ -d "$VIRTUAL_ENV" ]]
    then
        echo ".. found existing python3 venv in $VIRTUAL_ENV" >> $LOG_FILE 2>&1
    else
        mkdir -f $VIRTUAL_ENV >> $LOG_FILE 2>&1
    fi
    # force create environment
    python3 -m venv --clear --prompt py37 $VIRTUAL_ENV >> $LOG_FILE 2>&1
    # add to .bashrc
    if ! grep -q "source $VIRTUAL_ENV/bin/activate" "/home/$USER/.bashrc"; then
        echo "add source activate to .bashrc" >> $LOG_FILE 2>&1
        echo -e "\n# Multi-EAR python3 venv\nsource $VIRTUAL_ENV/bin/activate" | tee -a /home/$USER/.bashrc >> $LOG_FILE 2>&1
    else
        echo "source activate already exists in .bashrc" >> $LOG_FILE 2>&1
    fi
    do_activate_python3_venv
    echo ".. self-update pip" >> $LOG_FILE 2>&1
    $VIRTUAL_ENV/bin/python3 -m pip install --upgrade pip >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_activate_python3_venv
{
    echo ".. activate python3 venv" | tee -a $LOG_FILE
    source $VIRTUAL_ENV/bin/activate >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_python3_venv
{
    do_create_python3_venv
    # do_activate_python3_venv
}

#
# Systemd service actions
#
function do_systemd_service_unmask
{
    if systemctl -all list-unit-files $1.service | grep "$1.service masked" >/dev/null 2>&1;
    then
	sudo systemctl unmask $1.service >> $LOG_FILE 2>&1
    fi
}


function do_systemd_service_start
{
    if systemctl -all list-unit-files $1.service | grep "$1.service disabled" >/dev/null 2>&1;
    then
	sudo systemctl enable $1.service >> $LOG_FILE 2>&1
	sudo systemctl start $1.service >> $LOG_FILE 2>&1
    fi
}


function do_systemd_service_restart
{
    if [ "$(systemctl is-active $1)" == "active" ];
    then
        sudo systemctl restart $1.service >> $LOG_FILE 2>&1
    fi
}


function do_systemd_service_stop
{
    if systemctl -all list-unit-files $1.service | grep "$1.service enabled" >/dev/null 2>&1;
    then
	sudo systemctl disable $1.service >> $LOG_FILE 2>&1
	sudo systemctl stop $1.service >> $LOG_FILE 2>&1
    fi
}


#
# Configure
#
function do_rsync_etc
{
    echo ".. rsync /etc" | tee -a $LOG_FILE
    sudo rsync -amtv --chown=root:root etc / >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_init_log
{
    echo ".. init /var/log/multi-ear" | tee -a $LOG_FILE
    sudo mkdir -p /var/log/multi-ear >> $LOG_FILE 2>&1
    sudo chown -R $USER:$USER /var/log/multi-ear >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_rsyslog
{
    echo ".. configure rsyslog" | tee -a $LOG_FILE
    sudo mkdir -p /var/log/multi-ear >> $LOG_FILE 2>&1
    sudo chown -r $USER:$USER /var/log/multi-ear >> $LOG_FILE 2>&1
    sudo systemctl restart rsyslog >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_nginx
{
    echo ".. configure nginx" | tee -a $LOG_FILE
    # remove default nginx site
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo rm -f /etc/nginx/sites-available/default
    # unmask
    do_systemd_service_unmask "nginx"
    do_systemd_service_start "nginx"
    # test
    sudo service nginx configtest >> $LOG_FILE 2>&1
    # enable and start service
    do_systemd_service_restart "nginx"
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_dnsmasq
{
    echo ".. configure dnsmasq" | tee -a $LOG_FILE
    do_systemd_service_unmask "dnsmasq"
    do_systemd_service_stop "dnsmasq"
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_hostapd
{
    echo ".. configure hostapd" | tee -a $LOG_FILE
    sudo sed -i -s "s/^ssid=.*/ssid=$HOSTNAME/" /etc/hostapd/hostapd.conf >> $LOG_FILE 2>&1
    do_systemd_service_unmask "hostapd"
    do_systemd_service_stop "hostapd"
    # sudo systemctl disable hostapd >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_influxdb
{
    echo ".. configure influxdb" | tee -a $LOG_FILE
    # enable and start service
    do_systemd_service_unmask "influxdb"
    do_systemd_service_start "influxdb"
    # configure
    sudo cp etc/influxdb/influxdb.conf /etc/influxdb/influxdb.conf >> $LOG_FILE 2>&1
    # restart service
    do_systemd_service_restart "influxdb"
    echo -e ".. done\n" >> $LOG_FILE 2>&1

    # configure, enable service, create database
}


function do_configure_telegraf
{
    echo ".. configure telegraf" | tee -a $LOG_FILE
    # enable and start service
    do_systemd_service_unmask "telegraf"
    do_systemd_service_start "telegraf"
    # configure
    sudo cp etc/telegraf/telegraf.conf /etc/telegraf/telegraf.conf >> $LOG_FILE 2>&1
    # restart service
    do_systemd_service_restart "telegraf"
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_grafana
{
    echo ".. configure grafana" | tee -a $LOG_FILE
    # plugins 
    sudo grafana-cli plugins install grafana-clock-panel
    # enable and start service
    do_systemd_service_unmask "grafana"
    do_systemd_service_start "grafana"
    # configure
    sudo cp etc/grafana/grafana.conf /etc/grafana/grafana.ini >> $LOG_FILE 2>&1
    # restart service
    do_systemd_service_restart "grafana"
    echo -e ".. done\n" >> $LOG_FILE 2>&1

    # configure, enable service, link to database
}


function do_daemon_reload
{
    sudo systemctl daemon-reload >> $LOG_FILE 2>&1
}


function do_configure
{
    do_rsync_etc
    do_init_log
    do_daemon_reload
    do_configure_nginx
    do_configure_dnsmasq
    do_configure_hostapd
    do_configure_influxdb
    # do_configure_telegraf
    # do_configure_grafana
}


#
# Multi-EAR software
#
function do_gpio_watch_install
{
    echo ".. clone and make gpio-watch" | tee -a $LOG_FILE
    git clone https://github.com/larsks/gpio-watch.git >> $LOG_FILE 2>&1
    cd gpio-watch >> $LOG_FILE 2>&1
    make >> $LOG_FILE 2>&1
    cp gpio-watch $VIRTUAL_ENV/bin >> $LOG_FILE 2>&1
    cd .. >> $LOG_FILE 2>&1
    rm -rf gpio-watch >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_multi_ear_install
{
    do_activate_python3_venv

    local pip=$VIRTUAL_ENV/bin/pip3
    local python=$VIRTUAL_ENV/bin/python3
    local env_var 

    echo ".. pip install multi_ear" | tee -a $LOG_FILE
    $pip uninstall -y multi_ear_services . >> $LOG_FILE 2>&1
    $pip install . >> $LOG_FILE 2>&1
    # add to .bashrc
    env_var="FLASK_APP=multi_ear_services.ctrl"
    if ! grep -q "export $export_cmd" "/home/$USER/.bashrc";
    then
        echo "Add \"export $env_var\" to .bashrc" >> $LOG_FILE 2>&1
        echo "export $env_var" >> /home/$USER/.bashrc
    fi
    env_var="FLASK_ENV=production"
    if ! grep -q "export $env_var" "/home/$USER/.bashrc";
    then
        echo "Add \"export $env_var\" to .bashrc" >> $LOG_FILE 2>&1
        echo "export $env_var" >> /home/$USER/.bashrc
    fi

    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_multi_ear_services
{
    echo ".. setup multi-ear systemd services" | tee -a $LOG

    do_daemon_reload

    local services=$(ls etc/systemd/system)
    local service

    for service in $services
    do
        echo ".. setup systemd $service" >> $LOG_FILE 2>&1
        do_systemd_service $service >> $LOG_FILE 2>&1
        echo -e ".. done\n" >> $LOG_FILE 2>&1
    done
}


function do_systemd_service
{
    local service=$1

    local enabled=$( systemctl is-enabled $service )
    local active=$( systemctl is-active $service )

    if [ "$enabled" != "enabled" ];
    then
        sudo systemctl unmask $service >> $LOG_FILE 2>&1
        sudo systemctl enable $service >> $LOG_FILE 2>&1
    fi

    if [ "$active" != "active" ];
    then
        sudo systemctl start $service >> $LOG_FILE 2>&1
    else
        sudo systemctl restart $service >> $LOG_FILE 2>&1
    fi
}


function do_multi_ear
{
    do_activate_python3_venv
    do_multi_ear_install
    do_multi_ear_services
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


#
# Check if device is Raspberry Pi
#
isRaspberryPi


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


# Perform one step or the entire workflow
case "${1}" in
    all|'')
    rm -f $LOG_FILE
    echo "Multi-EAR Software Install Tool v${VERSION}" | tee $LOG_FILE
    do_install
    do_configure
    do_python3_venv
    do_multi_ear
    echo "Multi-EAR software install completed" | tee -a $LOG_FILE
    ;;
    packages) do_install
    ;;
    etc) do_rsync_etc
    ;;
    log) do_init_log
    ;;
    configure|config) do_configure
    ;;
    python|python3) do_python3_venv
    ;;
    multi-ear) do_multi_ear
    ;;
    *) badUsage "Unknown command ${1}." | tee $LOG_FILE
    ;;
esac

exit 0
