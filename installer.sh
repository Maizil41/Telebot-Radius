#!/bin/bash

opkg update
sleep 1
cd
sleep 1
opkg install git
opkg install git-http
sleep 1
opkg install python3
opkg install python3-pip
sleep 1
pip3 install pymysql python-telegram-bot
pip install python-telegram-bot[job-queue]
git clone https://github.com/Maizil41/Telebot-Radius.git
mv /root/Telebot-Radius/files/telebot /etc/init.d/
mv /root/Telebot-Radius/files/telebot.py /usr/bin/
chmod +x /usr/bin/telebot.py
chmod +x /etc/init.d/telebot
chmod +x /root/Telebot-Radius/files/*
sleep 5
service telebot enable
service telebot start
