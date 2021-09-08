#!/bin/bash

##############################################################################
# Script Name	: install.sh
# Description	: Automatic installation of the Multi-EAR :: info service.
# Args          : Python3 VIRTUAL_ENV path (default: /opt/py37) and log file
#                 (default: install.log).
# Author       	: Pieter Smets
# Email         : mail@pietersmets.be
##############################################################################

VIRTUAL_ENV="${1:-/opt/py37}"
LOG_FILE="${2:-install.log}"

SERVICE="multi-ear-info"
echo "$SERVICE.service install" | tee -a $LOG_FILE

if [ $(which python3) != "$VIRTUAL_ENV/bin/python3" ]; then
  source $VIRTUAL_ENV/bin/activate
  which python3
  which pip3
fi

echo ".. install packages" | tee -a $LOG_FILE
sudo apt install -y nginx >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. pip install python3 packages in $VIRTUAL_ENV" | tee -a $LOG_FILE
pip3 install uwsgi flask >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

DIR="/opt/services/$SERVICE"
echo ".. copy scripts to $DIR" | tee -a $LOG_FILE
mkdir -p $DIR >> $LOG_FILE 2>&1
cp uwsgi.ini $DIR >> $LOG_FILE 2>&1
cp info.py $DIR >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. setup nginx" | tee -a $LOG_FILE
sudo rm -f /etc/nginx/sites-available/default >> $LOG_FILE 2>&1
sudo rm -f /etc/nginx/sites-enabled/default >> $LOG_FILE 2>&1
sudo cp nginx.proxy /etc/nginx/sites-available/$SERVICE.proxy >> $LOG_FILE 2>&1
sudo ln -s -f /etc/nginx/sites-available/$SERVICE.proxy /etc/nginx/sites-enabled >> $LOG_FILE 2>&1
sudo service nginx configtest >> $LOG_FILE 2>&1
sudo service nginx restart >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. setup systemd service" | tee -a $LOG_FILE
sudo cp info.service /etc/systemd/system/$SERVICE.service >> $LOG_FILE 2>&1
sudo systemctl daemon-reload >> $LOG_FILE 2>&1
sudo systemctl enable $SERVICE >> $LOG_FILE 2>&1
sudo systemctl start $SERVICE >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo  ".. $SERVICE install complete" | tee -a $LOG_FILE
exit 0
