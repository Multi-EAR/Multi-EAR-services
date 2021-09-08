#!/bin/bash

##############################################################################
# Script Name	: install.sh
# Description	: Automatic software installation for the Multi-EAR platform
#                 given a prepared install of RASPBERRY PI OS LITE (32-bit).
# Args          : n.a.
# Author       	: Pieter Smets
# Email         : mail@pietersmets.be
##############################################################################

VERSION="0.1"
VIRTUAL_ENV="/opt/py37"
LOG_FILE="$(pwd)/install.log"

echo "Multi-EAR software install v$VERSION" | tee $LOG_FILE

# Check if current user is tud
if [ $USER != "tud" ]; then
  echo "Script must be run as user: tud" | tee -a $LOG_FILE
  exit -1
fi

# Check for default user pi
if id -u pi >/dev/null 2>&1; then
  echo "Default user pi should not exit" | tee -a $LOG_FILE
  exit -1
fi

echo ".. apt update" | tee -a $LOG_FILE
sudo apt update >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. apt upgrade" | tee -a $LOG_FILE
sudo apt upgrade -y >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. apt autoremove" | tee -a $LOG_FILE
sudo apt autoremove -y >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. apt install prerequisites" | tee -a $LOG_FILE
sudo apt install -y git wget build-essential checkinstall >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. apt install python3"
sudo apt install -y python3 python3-pip python3-venv >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. create python3 venv in $VIRTUAL_ENV" | tee -a $LOG_FILE
sudo mkdir $VIRTUAL_ENV >> $LOG_FILE 2>&1
sudo chown -R $USER:$USER $VIRTUAL_ENV >> $LOG_FILE 2>&1
python3 -m venv $VIRTUAL_ENV >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. activate python3 venv" | tee -a $LOG_FILE
if ! grep -q "source $VIRTUAL_ENV/bin/activate" "/home/$USER/.bashrc"; then
  echo "add source activate to .bashrc" >> $LOG_FILE 2>&1
  echo -e "\n# Multi-EAR python3 venv\nsource $VIRTUAL_ENV/bin/activate" | tee -a /home/$USER/.bashrc >> $LOG_FILE 2>&1
else
  echo "source activate already exists in .bashrc" >> $LOG_FILE 2>&1
fi
source $VIRTUAL_ENV/bin/activate >> $LOG_FILE 2>&1
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo ".. setup services" | tee -a $LOG_FILE
DIR="/opt/services"
sudo mkdir $DIR >> $LOG_FILE 2>&1
sudo chown -R $USER:$USER $DIR >> $LOG_FILE 2>&1
echo ".... multi-ear-uart.service" | tee -a $LOG_FILE
cd services/uart
bash install.sh $VIRTUAL_ENV $LOG_FILE
cd ../..
echo ".... multi-ear-info.service" | tee -a $LOG_FILE
cd services/info
bash install.sh $VIRTUAL_ENV $LOG_FILE
cd ../..
echo -e ".. done\n" >> $LOG_FILE 2>&1

echo  "install complete" | tee -a $LOG_FILE
