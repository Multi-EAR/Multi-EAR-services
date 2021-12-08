#!/bin/bash

##############################################################################
# Script Name	: multi-ear-services.sh
# Description	: Multi-EAR system services configuration for a deployed
#                 Raspberry Pi OS LITE (32-bit).
# Args          : [options] <install_step>
# Author       	: Pieter Smets
# Email         : mail@pietersmets.be
##############################################################################

# Name of the script
SCRIPT=$( basename "$0" )

# Current version from git
VERSION=$( git describe --tag --abbrev=0 2>&1 )

# Python virtual environment
PYTHON_ENV="/home/$USER/.py37"

# Bash environment for user
BASH_ENV="/home/$USER/.bashrc"

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
"Multi-EAR Services setup on a deployed Raspberry Pi OS LITE (32-bit)."
"Usage:"
"  $SCRIPT [options] <action>"
"Actions:"
"  install        Full installation of the Multi-Ear services:"
"                  * install Python3, dnsmasq, hostapd, nginx, influxdb, telegraf, grafana"
"                  * configure system services"
"                  * create Python3 virtual environment py37 in ~/.py37"
"                  * install and activate the Multi-EAR services"
"  check          Verify the installed Multi-EAR services and dependencies."
"  update         Update the existing Multi-EAR services and dependencies."
"  uninstall      Remove the installed Multi-EAR services, data, configurations and "
"                 the Python3 virtual environment."
"Options:"
"  --help, -h     Print help."
"  --version, -v  Print version."
""
"$SCRIPT only works on a Raspberry Pi platform."
"Environment variables \$MULTI_EAR_ID and \$MULTI_EAR_UUID should be defined in ~/.bashrc."
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
# Verbose helpers
#
function verbose_msg
{
    local message=$1
    local level=${2:-0}

    if [ $level -gt 0 ];
    then
        echo -e "$message" >> $LOG_FILE 2>&1
    else
        if [ "$LOG_FILE" == "/dev/stdout" ];
        then
            echo -e "$message"
        else
            echo -e "$message" | tee -a $LOG_FILE
        fi
    fi
}


function verbose_done
{
    if [ "$LOG_FILE" != "/dev/stdout" ];
    then
        echo -e ".. done\n" >> $LOG_FILE 2>&1
    fi
}


#
# Systemd service actions
#
function do_systemd_service_unmask
{
    if systemctl is-enabled $1 | grep "masked" >/dev/null 2>&1;
    then
        verbose_msg "systemctl unmask $1" 1
	sudo systemctl unmask $1 >> $LOG_FILE 2>&1
        systemctl is-enabled $1 >> $LOG_FILE 2>&1
    fi
}


function do_systemd_service_enable
{
    do_systemd_service_unmask $1

    if systemctl is-enabled $1 | grep "disabled" >/dev/null 2>&1;
    then
        verbose_msg "systemctl enable $1" 1
	sudo systemctl enable $1 >> $LOG_FILE 2>&1
        systemctl is-enabled $1 >> $LOG_FILE 2>&1
    fi
}


function do_systemd_service_disable
{
    do_systemd_service_unmask $1

    if systemctl is-enabled $1 | grep "enabled" >/dev/null 2>&1;
    then
        verbose_msg "systemctl disable $1" 1
	sudo systemctl disable $1 >> $LOG_FILE 2>&1
        systemctl is-enabled $1 >> $LOG_FILE 2>&1
    fi
}


function do_systemd_service_start
{
    if systemctl is-active $1 | grep "inactive" >/dev/null 2>&1;
    then
        verbose_msg "systemctl start $1" 1
	sudo systemctl start $1 >> $LOG_FILE 2>&1
        systemctl is-active $1 >> $LOG_FILE 2>&1
    fi
}


function do_systemd_service_stop
{
    if systemctl is-active $1 | grep "active" >/dev/null 2>&1;
    then
        verbose_msg "systemctl stop $1" 1
	sudo systemctl stop $1 >> $LOG_FILE 2>&1
        systemctl is-active $1 >> $LOG_FILE 2>&1
    fi
}


function do_systemd_service_restart
{
    if systemctl is-active $1 | grep "inactive" >/dev/null 2>&1;
    then
        verbose_msg "systemctl start $1" 1
	sudo systemctl start $1 >> $LOG_FILE 2>&1
        systemctl is-active $1 >> $LOG_FILE 2>&1
    else
        verbose_msg "systemctl restart $1" 1
        sudo systemctl restart $1 >> $LOG_FILE 2>&1
        systemctl is-active $1 >> $LOG_FILE 2>&1
    fi
}


function do_systemd_service_configtest
{
    # test configuration
    sudo service $1 configtest >> $LOG_FILE 2>&1

    # check exit code
    check_exit_code $? "service $1 configtest"
}


function do_systemd_env
{
    cat > $HOME/.multi_ear.env << EOF
MULTI_EAR_ID=$MULTI_EAR_ID
MULTI_EAR_UUID=$MULTI_EAR_UUID
MULTI_EAR_WIFI_SECRET=$MULTI_EAR_WIFI_SECRET
INFLUX_USERNAME=$INFLUX_USERNAME
INFLUX_PASSWORD=$INFLUX_PASSWORD
GRAFANA_USERNAME=$GRAFANA_USERNAME
GRAFANA_PASSWORD=$GRAFANA_PASSWORD
EOF
}


#
# Bashrc helpers
#
function is_environ_variable
{
    grep -q "export $1" $BASH_ENV >/dev/null 2>&1
}


function do_environ_variable_exists
{
    if ! is_environ_variable $1;
    then
        echo "Error: environment variable $1 does not exist!"
        exit -1
    fi
}


function do_export_environ_variable
{
    local VAR="$1" VALUE="$2"

    if is_environ_variable "$VAR='$VALUE'";
    then
        echo "$VAR already exists in $BASH_ENV" >> $LOG_FILE 2>&1
    else
        if is_environ_variable "$VAR=";
        then
            echo "$VAR updated in $BASH_ENV" >> $LOG_FILE 2>&1
            sed -i -s "s/^export $VAR=.*/export $VAR='$VALUE'/" $BASH_ENV >> $LOG_FILE 2>&1
        else
            echo "$VAR added to $BASH_ENV" >> $LOG_FILE 2>&1
            echo "export $VAR='$VALUE'" >> $BASH_ENV
        fi
    fi
}


#
# Installs
#
function do_install_libs
{
    verbose_msg ".. install libs"
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y libatlas-base-dev >> $LOG_FILE 2>&1
    sudo apt install -y build-essential libssl-dev libffi-dev >> $LOG_FILE 2>&1
    verbose_done
}


function do_install_python3
{
    verbose_msg echo ".. install python3"
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
    verbose_done
}


function do_install_nginx
{
    verbose_msg ".. install nginx"
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y nginx >> $LOG_FILE 2>&1
    verbose_done
}


function do_install_hostapd
{
    verbose_msg ".. install hostapd"
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y hostapd >> $LOG_FILE 2>&1
    verbose_done
}


function do_install_dnsmasq
{
    verbose_msg ".. install dnsmasq"
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y dnsmasq >> $LOG_FILE 2>&1
    sudo apt purge -y dns-root-data >> $LOG_FILE 2>&1
    verbose_done
}


function do_install_influxdb_telegraf
{
    verbose_msg ".. install influxdb & telegraf"
    # add to apt
    wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add - >> $LOG_FILE 2>&1
    echo "deb https://repos.influxdata.com/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list >> $LOG_FILE 2>&1
    # install
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y influxdb telegraf >> $LOG_FILE 2>&1
    # done
    verbose_done
}


function do_install_grafana
{
    verbose_msg ".. install grafana"
    # add to apt
    curl -s https://packages.grafana.com/gpg.key | sudo apt-key add - >> $LOG_FILE 2>&1
    echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list >> $LOG_FILE 2>&1
    # install
    sudo apt update >> $LOG_FILE 2>&1
    sudo apt install -y grafana >> $LOG_FILE 2>&1
    verbose_done
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
    verbose_msg ".. create python3 venv in $PYTHON_ENV"

    # check if already exists
    if [[ -d "$PYTHON_ENV" ]]
    then
        echo ".. found existing python3 venv in $PYTHON_ENV" >> $LOG_FILE 2>&1
    else
        mkdir -f $PYTHON_ENV >> $LOG_FILE 2>&1
    fi

    # force create environment
    /usr/bin/python3 -m venv --clear --prompt py37 $PYTHON_ENV >> $LOG_FILE 2>&1

    # add virtual environment activation to .bashrc
    if ! grep -q "source $PYTHON_ENV/bin/activate" $BASH_ENV; then
        echo "add source activate to $BASH_ENV" >> $LOG_FILE 2>&1
        echo -e "\n# Multi-EAR python3 venv\nsource $PYTHON_ENV/bin/activate" | tee -a $BASH_ENV >> $LOG_FILE 2>&1
    else
        echo "source activate already exists in $BASH_ENV" >> $LOG_FILE 2>&1
    fi

    # activate
    do_activate_python3_venv

    # update pip
    verbose_msg ".. self-update pip"
    local PIP="$PYTHON_ENV/bin/python3 -m pip install"
    $PIP --upgrade pip >> $LOG_FILE 2>&1

    # add build packages for offline installation
    verbose_msg ".. pre-install build-system requirements" 
    $PIP install "setuptools>=45" --upgrade >> $LOG_FILE 2>&1
    $PIP install "setuptools_scm>=6.2" --upgrade >> $LOG_FILE 2>&1
    $PIP install "wheel" --upgrade >> $LOG_FILE 2>&1

    verbose_done
}


function do_activate_python3_venv
{
    verbose_msg ".. activate python3 venv"
    source $PYTHON_ENV/bin/activate >> $LOG_FILE 2>&1
    verbose_done
}


#
# Configure
#
function do_rsync_etc
{
    verbose_msg ".. rsync /etc"
    # rsync
    sudo rsync -amtv --chown=root:root etc / >> $LOG_FILE 2>&1
    check_exit_code $? "rsync /etc"
    # replace ssid by hostname in hostapd
    sudo sed -i -s "s/^ssid=.*/ssid=$HOSTNAME/" /etc/hostapd/hostapd.conf >> $LOG_FILE 2>&1
    verbose_done
}


function do_configure_rsyslog
{
    verbose_msg ".. configure rsyslog"
    sudo mkdir -p /var/log/multi-ear >> $LOG_FILE 2>&1
    sudo chown -R $USER:$USER /var/log/multi-ear >> $LOG_FILE 2>&1
    do_systemd_service_restart "rsyslog"
    verbose_done
}


function do_configure_nginx
{
    verbose_msg ".. configure nginx"
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
    verbose_done
}


function do_configure_dnsmasq
{
    verbose_msg ".. configure dnsmasq"
    sudo systemctl reset-failed "dnsmasq.service" >> $LOG_FILE 2>&1
    do_systemd_service_disable "dnsmasq.service"
    do_systemd_service_stop "dnsmasq.service"
    verbose_done
}


function do_configure_hostapd
{
    verbose_msg ".. configure hostapd"
    # stop service
    sudo systemctl reset-failed "hostapd.service" >> $LOG_FILE 2>&1
    do_systemd_service_disable "hostapd.service"
    do_systemd_service_stop "hostapd.service"
    # replace ssid by hostname 
    sudo sed -i -s "s/^ssid=.*/ssid=$HOSTNAME/" /etc/hostapd/hostapd.conf >> $LOG_FILE 2>&1
    # done
    verbose_done
}


function influx_e
{
    if [ $# -eq 1 ]; then
        verbose_msg "> $1" 1
        influx -execute "$1" >> $LOG_FILE 2>&1
    else
        verbose_msg "> $1 @ $2" 1
        influx -execute "$1" -database "$2" >> $LOG_FILE 2>&1
    fi
}


function do_configure_influxdb
{
    verbose_msg ".. configure influxdb"

    # enable
    do_systemd_service_enable "influxdb.service"

    # link default settings
    verbose_msg "> enable default configuration" 1
    sudo ln -sf /etc/influxdb/default.conf /etc/influxdb/influxdb.conf >> $LOG_FILE 2>&1

    # restart with default settings
    do_systemd_service_restart "influxdb.service"

    # logging and output
    sudo mkdir -p /var/log/influxdb /var/lib/influxdb
    sudo chown -R influxdb:influxdb /var/log/influxdb /var/lib/influxdb
    sudo chmod 755 /var/log/influxdb /var/lib/influxdb

    #
    # influx query docs: https://docs.influxdata.com/influxdb/v1.8/
    #

    # remove default internal database for logging
    influx_e "DROP DATABASE '_internal'"

    # create retention policies
    local rp_m="one_month" rp_m_specs="DURATION 30d REPLICATION 1 SHARD DURATION 1d DEFAULT"
    local rp_y="one_year"  rp_y_specs="DURATION 52w REPLICATION 1 SHARD DURATION 1d DEFAULT"

    # create database telegraf?
    if ! influx -execute "SHOW DATABASES" | grep -q "telegraf";
    then
        influx_e "CREATE DATABASE telegraf"
    fi
    influx_e "CREATE RETENTION POLICY $rp_m ON telegraf $rp_m_specs"

    # create databases multi_ear?
    if ! influx -execute "SHOW DATABASES" | grep -q "multi_ear";
    then
        influx_e "CREATE DATABASE multi_ear"
    fi
    influx_e "CREATE RETENTION POLICY $rp_y ON multi_ear $rp_y_specs"

    # create full-privilege user
    if [ "$INFLUX_USERNAME" == "" ];
    then
        INFLUX_USERNAME="${USER}_influx"
        do_export_environ_variable "INFLUX_USERNAME" "$INFLUX_USERNAME"
    fi
    if [ "$INFLUX_PASSWORD" == "" ] ;
    then
        INFLUX_PASSWORD="$(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c20)"
        do_export_environ_variable "INFLUX_PASSWORD" "$INFLUX_PASSWORD"
    fi
    if ! influx -execute "show users" | grep -q "$INFLUX_USERNAME";
    then
        influx_e "CREATE USER $INFLUX_USERNAME WITH PASSWORD '$INFLUX_PASSWORD' WITH ALL PRIVILEGES"
    fi
    influx_e "GRANT ALL PRIVILEGES ON multi_ear TO $INFLUX_USERNAME"
    influx_e "GRANT ALL PRIVILEGES ON telegraf TO $INFLUX_USERNAME"

    # create read-only user
    if ! influx -execute "show users" | grep -q "ear";
    then
        influx_e "CREATE USER ear WITH PASSWORD 'listener'"
    fi

    # revoke read-only user permissions
    influx_e "REVOKE ALL PRIVILEGES FROM ear"
    influx_e "GRANT READ ON multi_ear TO ear"
    influx_e "GRANT READ ON telegraf TO ear"

    # enforce multi-ear settings (requires login from now on!)
    verbose_msg "> enable multi-ear configuration" 1
    sudo ln -sf /etc/influxdb/multi-ear.conf /etc/influxdb/influxdb.conf >> $LOG_FILE 2>&1

    # restart service
    do_systemd_service_restart "influxdb"

    # done
    verbose_done
}


function do_configure_telegraf
{
    verbose_msg ".. configure telegraf"
    # start and enable service
    do_systemd_service_start "telegraf"
    do_systemd_service_enable "telegraf"
    # logging and output
    sudo mkdir -p /var/log/telegraf /var/lib/telegraf
    sudo chown -R telegraf:telegraf /var/log/telegraf /var/lib/telegraf
    sudo chmod 755 /var/log/telegraf /var/lib/telegraf
    # restart service
    do_systemd_service_restart "telegraf"
    verbose_done
}


function do_configure_grafana
{
    verbose_msg ".. configure grafana"
    # create local admin
    if [ "$GRAFANA_USERNAME" == "" ];
    then
        GRAFANA_USERNAME="${USER}_grafana"
        do_export_environ_variable "GRAFANA_USERNAME" "$GRAFANA_USERNAME"
    fi
    if [ "$GRAFANA_PASSWORD" == "" ] ;
    then
        GRAFANA_PASSWORD="$(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c20)"
        do_export_environ_variable "GRAFANA_PASSWORD" "$GRAFANA_PASSWORD"
    fi
    # grafana-cli docs: https://grafana.com/docs/grafana/latest/administration/cli/
    # start and enable service
    do_systemd_service_start "grafana-server"
    do_systemd_service_enable "grafana-server"
    # logging and output
    sudo mkdir -p /var/log/grafana /var/lib/grafana /var/lib/grafana/plugins
    sudo chown -R grafana:grafana /var/log/grafana /var/lib/grafana /var/lib/grafana/plugins
    sudo chmod 755 /var/log/grafana /var/lib/grafana /var/lib/grafana/plugins
    # set password
    sudo grafana-cli admin reset-admin-password $GRAFANA_PASSWORD >> $LOG_FILE 2>&1
    # install plugins
    sudo grafana-cli plugins install grafana-clock-panel >> $LOG_FILE 2>&1
    # add dashboards!
    # restart service
    do_systemd_service_restart "grafana-server"
    # done
    verbose_done
}


function do_daemon_reload
{
    sudo systemctl daemon-reload >> $LOG_FILE 2>&1
    sudo systemctl reset-failed >> $LOG_FILE 2>&1
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
    do_systemd_env
}


#
# Multi-EAR software
#
function do_gpio_watch_install
{
    return # Currently not needed but will be usefull to silence wlan autohotspot via a jumper

    do_activate_python3_venv

    verbose_msg ".. clone and make gpio-watch"
    git clone https://github.com/larsks/gpio-watch.git >> $LOG_FILE 2>&1
    cd gpio-watch >> $LOG_FILE 2>&1
    make >> $LOG_FILE 2>&1
    cp gpio-watch $PYTHON_ENV/bin >> $LOG_FILE 2>&1
    cd .. >> $LOG_FILE 2>&1
    rm -rf gpio-watch >> $LOG_FILE 2>&1

    verbose_done
}


function do_multi_ear_services
{
    do_activate_python3_venv

    local pip=$PYTHON_ENV/bin/pip3
    local python=$PYTHON_ENV/bin/python3

    # remove and install services
    verbose_msg ".. pip install multi_ear_services"
    $pip uninstall -y multi_ear_services . >> $LOG_FILE 2>&1
    $pip install . >> $LOG_FILE 2>&1

    # set default wifi secret
    if [ "$MULTI_EAR_WIFI_SECRET" == "" ];
    then
        do_export_environ_variable "MULTI_EAR_WIFI_SECRET" "albatross"
    fi

    # Start and enable services
    ## multi-ear-ctrl
    do_systemd_service_enable "multi-ear-ctrl.service"
    do_systemd_service_restart "multi-ear-ctrl.service"
    do_export_environ_variable "FLASK_APP" "multi_ear_services.ctrl"
    do_export_environ_variable "FLASK_ENV" "production"
    ## multi-ear-wifi
    do_systemd_service_enable "multi-ear-wifi.service"
    do_systemd_service_start "multi-ear-wifi.service"
    ## multi-ear-uart
    do_systemd_service_enable "multi-ear-uart.service"
    do_systemd_service_start "multi-ear-uart.service"

    # done
    verbose_done
}


#
# Uninstall
#
function do_update
{
    # update repository --> should become optional
    # git pull

    # Rsync configure
    do_rsync_etc

    # Restart 3rd party services
    do_systemd_service_restart "rsyslog"
    do_systemd_service_restart "nginx"
    do_systemd_service_restart "influxdb"
    do_systemd_service_restart "telegraf"
    do_systemd_service_restart "grafana-server"

    # Pip multi-ear services
    $pip uninstall -y multi_ear_services . >> $LOG_FILE 2>&1
    $pip install . >> $LOG_FILE 2>&1

    # Restart multi-ear services
    do_systemd_service_restart "multi-ear-ctrl.service"
    do_systemd_service_restart "multi-ear-uart.service"
}


#
# Check
#
function do_check
{
    echo "Not implementen yet."
    exit -1
}


#
# Uninstall
#
function do_uninstall
{
    # Stop and disable services
    ## multi-ear-ctrl
    do_systemd_service_stop "multi-ear-ctrl.service"
    do_systemd_service_disable "multi-ear-ctrl.service"
    ## multi-ear-wifi
    do_systemd_service_stop "multi-ear-wifi.service"
    do_systemd_service_disable "multi-ear-wifi.service"
    ## multi-ear-uart
    do_systemd_service_stop "multi-ear-uart.service"
    do_systemd_service_disable "multi-ear-uart.service"

    # Enable wpa_supplicant
    sudo sed -i -s "s/^nohook wpa_supplicant/#nohook wpa_supplicant/" /etc/dhcpcd.conf >> $LOG_FILE 2>&1

    # Nginx proxy
    sudo rm /etc/nginx/sites-available/multi-ear-ctrl.proxy
    sudo rm /etc/nginx/sites-enabled/multi-ear-ctrl.proxy
    do_systemd_service_restart "nginx"

    # Rsyslog
    sudo rm /etc/rsyslog.d/multi-ear.conf
    do_systemd_service_restart "rsyslog"

    # InfluxDB
    ## link default settings
    verbose_msg "> enable default configuration" 1
    sudo ln -sf /etc/influxdb/default.conf /etc/influxdb/influxdb.conf >> $LOG_FILE 2>&1
    ## restart with default settings
    do_systemd_service_restart "influxdb.service"
    ## Remove Influx Database
    influx_e "DROP DATABASE 'multi_ear'"

    # Disable venv activation and remove folder
    sudo sed -i -s "s/^source \/home\/tud\/.py37\/bin\/activate/#source \/home\/tud\/.py37\/bin\/activate/" $HOME/.bashrc >> $LOG_FILE 2>&1
    rm -rf $HOME/.py37
}


#
# Process options
#
while (( $# ));
do
    case "$1" in
        --help|-h|help) usage
        ;;
        --version|-v|version) version
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
    echo "Script must be run as user: tud"
    exit -1
fi


#
# Check for default user pi
#
if id -u pi >/dev/null 2>&1; then
    echo "Default user pi should not exit"
    exit -1
fi


#
# Check for identifiers in bash environment
#
do_environ_variable_exists 'MULTI_EAR_ID'
do_environ_variable_exists 'MULTI_EAR_UUID'


#
# Backup bash environment once
#
if [ ! -f $BASH_ENV.old ]; then cp $BASH_ENV $BASH_ENV.old; fi


# Perform one step or the entire workflow
case "$1" in
    install)
    rm -f $LOG_FILE
    verbose_msg "Multi-EAR Services ${VERSION}"
    do_install
    do_py37_venv
    do_configure
    do_multi_ear_services
    verbose_msg "Multi-EAR services install completed"
    ;;
    configure)
    do_configure
    do_multi_ear_services
    ;;
    check) do_check
    ;;
    update) do_update
    ;;
    uninstall) do_uninstall
    ;;
    do_*) LOG_FILE=/dev/stdout; $@;  # internal function calls for development (stdout-only)
    ;;
    *) badUsage "Unknown command ${1}." | tee $LOG_FILE
    ;;
esac


exit 0
