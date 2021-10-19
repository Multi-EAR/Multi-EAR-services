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
    if cat /proc/device-tree/model 2>&1 | tr '\0' '\n' | grep "Raspberry Pi" >/dev/null 2>&1;
    then
        return
    else
        echo "Error: device is not a Raspberry Pi!"
        exit -1
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
"  py37           Create the Python3 virtual environment."
"  configure      Sync /etc and configure all packages."
"  services       Install (pip) and enable the Multi-EAR services."
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
# Check exit code
#
function check_exit_code
{
    local code=${1:-$?}
    local command="${2:-Command}"

    if [ $code != 0 ];
    then
        printf "** Error ** : $command failed with exit code $code. Install terminated.\n\n"
        exit -1
    fi
}


#
# Systemd service actions
#
function do_systemd_service_unmask
{
    if systemctl is-enabled $1 | grep "masked" >/dev/null 2>&1;
    then
	sudo systemctl unmask $1 >> $LOG_FILE 2>&1
    fi
    systemctl status $1 >> $LOG_FILE 2>&1
}


function do_systemd_service_enable
{
    do_systemd_service_unmask $1

    if systemctl is-enabled $1 | grep "disabled" >/dev/null 2>&1;
    then
	sudo systemctl enable $1 >> $LOG_FILE 2>&1
    fi
    systemctl status $1 >> $LOG_FILE 2>&1
}


function do_systemd_service_disable
{
    do_systemd_service_unmask $1

    if systemctl is-enabled $1 | grep "enabled" >/dev/null 2>&1;
    then
	sudo systemctl disable $1 >> $LOG_FILE 2>&1
    fi
    systemctl status $1 >> $LOG_FILE 2>&1
}


function do_systemd_service_start
{
    if systemctl is-active $1 | grep "inactive" >/dev/null 2>&1;
    then
	sudo systemctl start $1 >> $LOG_FILE 2>&1
    fi
    systemctl status $1 >> $LOG_FILE 2>&1
}


function do_systemd_service_stop
{
    if systemctl is-active $1 | grep "active" >/dev/null 2>&1;
    then
	sudo systemctl stop $1 >> $LOG_FILE 2>&1
    fi
    systemctl status $1 >> $LOG_FILE 2>&1
}


function do_systemd_service_restart
{
    if systemctl is-active $1 | grep "inactive" >/dev/null 2>&1;
    then
	sudo systemctl start $1 >> $LOG_FILE 2>&1
    else
        sudo systemctl restart $1 >> $LOG_FILE 2>&1
    fi
    systemctl status $1 >> $LOG_FILE 2>&1
}


function do_systemd_service_configtest
{
    # test configuration
    sudo service $1 configtest >> $LOG_FILE 2>&1

    # check exit code
    check_exit_code $? "service $1 configtest"
}


#
# Bashrc helpers
#
function export_environment_variable
{
    local VAR="$1"
    local VALUE="$2"

    if grep -q "export $VAR=$VALUE" /home/$USER/.bashrc >/dev/null 2>&1;
    then
        echo "export $VAR=$VALUE already exists in .bashrc" >> $LOG_FILE 2>&1
    else
        if grep -q "export $VAR=" /home/$USER/.bashrc >/dev/null 2>&1;
        then
            echo "export $VAR=$VALUE updated in .bashrc" >> $LOG_FILE 2>&1
            sed -i -s "s/^export $VAR=.*/export $VAR=$VALUE/" /home/$USER/.bashrc >> $LOG_FILE 2>&1
        else
            echo "export $VAR=$VALUE added to .bashrc" >> $LOG_FILE 2>&1
            echo "export $VAR=$VALUE" >> /home/$USER/.bashrc
        fi
    fi
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
function do_py37_venv
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
    /usr/bin/python3 -m venv --clear --prompt py37 $VIRTUAL_ENV >> $LOG_FILE 2>&1

    # add virtual environment activation to .bashrc
    if ! grep -q "source $VIRTUAL_ENV/bin/activate" /home/$USER/.bashrc; then
        echo "add source activate to .bashrc" >> $LOG_FILE 2>&1
        echo -e "\n# Multi-EAR python3 venv\nsource $VIRTUAL_ENV/bin/activate" | tee -a /home/$USER/.bashrc >> $LOG_FILE 2>&1
    else
        echo "source activate already exists in .bashrc" >> $LOG_FILE 2>&1
    fi

    # activate
    do_activate_python3_venv

    # update pip
    echo ".. self-update pip" | tee -a $LOG_FILE

    local PIP="$VIRTUAL_ENV/bin/python3 -m pip install"
    $PIP --upgrade pip >> $LOG_FILE 2>&1

    # add build packages for offline installation
    echo ".. pre-install build-system requirements" | tee -a $LOG_FILE
    $PIP install "setuptools>=45" --upgrade >> $LOG_FILE 2>&1
    $PIP install "setuptools_scm>=6.2" --upgrade >> $LOG_FILE 2>&1
    $PIP install "wheel" --upgrade >> $LOG_FILE 2>&1

    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_activate_python3_venv
{
    echo ".. activate python3 venv" | tee -a $LOG_FILE
    source $VIRTUAL_ENV/bin/activate >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


#
# Configure
#
function do_rsync_etc
{
    # rsync specific folder in /etc
    sudo rsync -amtv --chown=root:root etc / >> $LOG_FILE 2>&1
    # check exit code
    check_exit_code $? "rsync /etc"
}


function do_configure_rsyslog
{
    echo ".. configure rsyslog" | tee -a $LOG_FILE
    # create log directory
    sudo mkdir -p /var/log/multi-ear >> $LOG_FILE 2>&1
    sudo chown -R $USER:$USER /var/log/multi-ear >> $LOG_FILE 2>&1
    # restart service
    do_systemd_service_restart "rsyslog"
    # done
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_nginx
{
    echo ".. configure nginx" | tee -a $LOG_FILE
    # remove default nginx site
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo rm -f /etc/nginx/sites-available/default
    # enable service
    do_systemd_service_enable "nginx.service"
    # test config
    do_systemd_service_configtest "nginx"
    # restart service
    do_systemd_service_restart "nginx.service"
    # done
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_dnsmasq
{
    echo ".. configure dnsmasq" | tee -a $LOG_FILE
    # stop service
    do_systemd_service_stop "dnsmasq.service"
    # done
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_hostapd
{
    echo ".. configure hostapd" | tee -a $LOG_FILE
    # stop service
    do_systemd_service_stop "hostapd.service"
    # replace ssid by hostname 
    sudo sed -i -s "s/^ssid=.*/ssid=$HOSTNAME/" /etc/hostapd/hostapd.conf >> $LOG_FILE 2>&1
    # done
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_influxdb
{
    echo ".. configure influxdb" | tee -a $LOG_FILE
    # enable and force start service (with default configuration!)
    do_systemd_service_enable "influxdb.service"
    do_systemd_service_restart "influxdb.service"
    # influx docs: https://docs.influxdata.com/influxdb/v1.8/
    # create local admin
    local INFLUX_USERNAME="${USER}_influx"
    export_environment_variable "INFLUX_USERNAME" "$INFLUX_USERNAME"
    local INFLUX_PASSWORD="$(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c20)"
    export_environment_variable "INFLUX_PASSWORD" "$INFLUX_PASSWORD"
    # local INFLUXDB_HTTP_SHARED_SECRET="$(echo $INFLUX_PASSWORD | shasum | head -c40 | base64 | head -c54)"
    # export_environment_variable "INFLUXDB_HTTP_SHARED_SECRET" "$INFLUXDB_HTTP_SHARED_SECRET"
    # create database and users
    echo ".. create influx database and users" >> $LOG_FILE
    local cmd
    local influx_cmds=(
        "CREATE DATABASE multi_ear"
        "SHOW DATABASES"
        "USE multi_ear"
        "CREATE RETENTION POLICY oneyear ON multi_ear DURATION 366d REPLICATION 1 SHARD DURATION 7d"
        "CREATE USER $INFLUX_USERNAME WITH PASSWORD '$INFLUX_PASSWORD' WITH ALL PRIVILEGES"
        "GRANT ALL PRIVILEGES ON multi_ear TO $INFLUX_USERNAME"
        "GRANT ALL PRIVILEGES ON telegraf TO $INFLUX_USERNAME"
        "SHOW GRANTS FOR $INFLUX_USERNAME"
        "CREATE USER ear WITH PASSWORD 'listener'"
        "GRANT READ ON multi_ear TO ear"
        "SHOW GRANTS FOR ear"
        "SHOW USERS"
    )
    for cmd in "${influx_cmds[@]}"
    do
        echo ".... influx -execute \"$cmd\"" >> $LOG_FILE
        influx -execute "$cmd" >> $LOG_FILE 2>&1
    done
    # enforce multi-ear settings (requires login from now on!)
    sudo mv /etc/influxdb/multi-ear.conf /etc/influxdb/influxdb.conf >> $LOG_FILE 2>&1
    # restart service
    do_systemd_service_restart "influxdb"
    # done
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_telegraf
{
    echo ".. configure telegraf" | tee -a $LOG_FILE
    # enable and forece start service 
    do_systemd_service_enable "telegraf"
    do_systemd_service_restart "telegraf"
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_configure_grafana
{
    echo ".. configure grafana" | tee -a $LOG_FILE
    # enable service 
    do_systemd_service_enable "grafana"
    # grafana-cli docs: https://grafana.com/docs/grafana/latest/administration/cli/
    # create local admin
    local GRAFANA_USERNAME="${USER}_grafana"
    export_environment_variable "GRAFANA_USERNAME" "$GRAFANA_USERNAME"
    local GRAFANA_PASSWORD='$(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c20)'
    export_environment_variable "GRAFANA_PASSWORD" "$GRAFANA_PASSWORD"
    # set password
    sudo grafana-cli admin reset-admin-password $GRAFANA_PASSWORD >> $LOG_FILE 2>&1
    # install plugins
    sudo grafana-cli plugins install grafana-clock-panel
    # add dashboards!
    # force start serice
    do_systemd_service_restart "grafana"
    # done
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_daemon_reload
{
    sudo systemctl daemon-reload >> $LOG_FILE 2>&1
    # sudo systemctl reset-failed >> $LOG_FILE 2>&1
}


function do_configure
{
    do_rsync_etc
    do_daemon_reload
    do_configure_rsyslog
    do_configure_nginx
    do_configure_dnsmasq
    do_configure_hostapd
    do_configure_influxdb
    do_configure_telegraf
    do_configure_grafana
}


#
# Multi-EAR software
#
function do_gpio_watch_install
{
    return # Currently not needed but will be usefull to silence wlan autohotspot via a jumper

    do_activate_python3_venv

    echo ".. clone and make gpio-watch" | tee -a $LOG_FILE
    git clone https://github.com/larsks/gpio-watch.git >> $LOG_FILE 2>&1
    cd gpio-watch >> $LOG_FILE 2>&1
    make >> $LOG_FILE 2>&1
    cp gpio-watch $VIRTUAL_ENV/bin >> $LOG_FILE 2>&1
    cd .. >> $LOG_FILE 2>&1
    rm -rf gpio-watch >> $LOG_FILE 2>&1
    echo -e ".. done\n" >> $LOG_FILE 2>&1
}


function do_multi_ear_services
{
    do_activate_python3_venv

    local pip=$VIRTUAL_ENV/bin/pip3
    local python=$VIRTUAL_ENV/bin/python3

    # remove and install services
    echo ".. pip install multi_ear_services" | tee -a $LOG_FILE
    $pip uninstall -y multi_ear_services . >> $LOG_FILE 2>&1
    $pip install . >> $LOG_FILE 2>&1

    # multi-ear-ctrl
    do_systemd_service_enable "multi-ear-ctrl.service"
    do_systemd_service_restart "multi-ear-ctrl.service"
    export_environment_variable "FLASK_APP" "multi_ear_services.ctrl"
    export_environment_variable "FLASK_ENV" "production"

    # multi-ear-wifi
    do_systemd_service_enable "multi-ear-wifi.service"
    do_systemd_service_start "multi-ear-wifi.service"

    # multi-ear-uart
    do_systemd_service_enable "multi-ear-uart.service"
    do_systemd_service_start "multi-ear-uart.service"

    echo -e ".. done\n" >> $LOG_FILE 2>&1
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

#
# Backup .bashrc
#
cp /home/tud/.bashrc /home/tud/.bashrc.old


# Perform one step or the entire workflow
case "${1}" in
    all|'')
    rm -f $LOG_FILE
    echo "Multi-EAR Software Install Tool v${VERSION}" | tee $LOG_FILE
    do_install
    do_py37_venv
    do_configure
    do_multi_ear_services
    echo "Multi-EAR software install completed" | tee -a $LOG_FILE
    ;;
    packages) do_install
    ;;
    py37) do_py37_venv
    ;;
    configure|config) do_configure
    ;;
    services) do_multi_ear_services
    ;;
    *) badUsage "Unknown command ${1}." | tee $LOG_FILE
    ;;
esac

exit 0
