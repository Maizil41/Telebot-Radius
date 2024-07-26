#!/bin/bash

echo "UPDATE REPOSITORY"
sleep 1
opkg update
clear
echo "SUCCESS"
clear
sleep 1
cd
echo "INSTALLING GIT"
sleep 1
opkg install git
opkg install git-http
clear
echo "SUCCESS"
clear
sleep 1
echo "INSTALLING PYTHON"
sleep 1
opkg install python3
opkg install python3-venv
opkg install python3-pip
clear
echo "SUCCESS"
clear
sleep 1
echo "INSTALLING JQ"
sleep 1
opkg install jq
clear
echo "SUCCESS"
clear
sleep 1
echo "INSTALLING SYSSTAT"
sleep 1
opkg install sysstat
clear
echo "SUCCESS"
clear
sleep 1
echo "INSTALLING TOOLS ...."
sleep 2
pip3 install telepot requests python-telegram-bot python-filter pymysql
git clone https://github.com/Maizil41/Telebot-Radius.git
mv /root/Telebot-Radius/files/telebot /etc/init.d/
mv /root/Telebot-Radius/files/telebot.py /usr/bin/
chmod +x /usr/bin/telebot.py
chmod +x /etc/init.d/telebot
chmod +x /root/Telebot-Radius/files/*
clear
echo "SUCCESS"
clear
sleep 1
echo "SETUP TOOLS ....."
sleep 5
clear
echo "
             ___  ____   _ _____ _____  ___  ______  ___  
             |  \/  | | | |_   _|_   _|/ _ \ | ___ \/ _ \ 
             | .  . | | | | | |   | | / /_\ \| |_/ / /_\ \
             | |\/| | | | | | |   | | |  _  ||    /|  _  |
             | |  | | |_| | | |  _| |_| | | || |\ \| | | |
             \_|  |_/\___/  \_/  \___/\_| |_/\_| \_\_| |_/
                    W I R E L E S S - F R E E D O M
───────────────────────────────────────────────────────────────────────
echo "[+] THAKS FOR USE MY TOOLS & SUPPORT ME :)"
service telebot enable
service telebot start