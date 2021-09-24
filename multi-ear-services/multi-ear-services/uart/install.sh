#!/bin/bash

##############################################################################
# Script Name	: install.sh
# Description	: Automatic installation of the Multi-EAR :: uart service.
# Args          : Python3 VIRTUAL_ENV path (default: /opt/py37) and log file
#                 (default: install.log)
# Author       	: Pieter Smets
# Email         : mail@pietersmets.be
##############################################################################

VIRTUAL_ENV="${1:-/opt/py37}"
LOG_FILE="${2:-install.log}"

SERVICE="multi-ear-uart"
echo "$SERVICE install" | tee -a $LOG_FILE

if [ $(which python3) != "$VIRTUAL_ENV/bin/python3" ]; then
  source $VIRTUAL_ENV/bin/activate >> $LOG_FILE 2>&1
  which python3 >> $LOG_FILE 2>&1
  which pip3 >> $LOG_FILE 2>&1
fi

echo ".. install packages" | tee -a $LOG_FILE
sudo apt install -y python3-gpiozero python3-serial >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. pip install python3 packages in $VIRTUAL_ENV" | tee -a $LOG_FILE
python3 -m pip install pyserial >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

DIR="/opt/services/$SERVICE"
echo ".. copy scripts to $DIR" | tee -a $LOG_FILE
mkdir -p $DIR >> $LOG_FILE 2>&1
cp uart.py $DIR >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. setup systemd service" | tee -a $LOG
sudo systemctl stop $SERVICE >> $LOG_FILE 2>&1
sudo cp uart.service /etc/systemd/system/$SERVICE.service >> $LOG_FILE 2>&1
sudo systemctl daemon-reload >> $LOG_FILE 2>&1
sudo systemctl enable $SERVICE >> $LOG_FILE 2>&1
sudo systemctl start $SERVICE >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo  ".. $SERVICE install complete" | tee -a $LOG_FILE
exit 0
