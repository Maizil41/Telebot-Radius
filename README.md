### TELEGRAM BOT FOR OPENWRT DALORADIUS

* [**OWNER**](https://t.me/maizil41)
========================================================================
##### MANUAL INSTALL
```
opkg update
```
```
opkg install git git-http python3 python3-pip
```
```
pip3 install pymysql python-telegram-bot
```
```
pip install python-telegram-bot[job-queue]
```
===========================================================================
##### CLONE REPOSITORY
```
git clone https://github.com/Maizil41/Telebot-Radius.git
```
##### MOVE ALL SCRIPT
```
mv /root/Telebot-Radius/files/telebot /etc/init.d/ && mv /root/Telebot-Radius/files/telebot.py /usr/bin/ && chmod +x /usr/bin/telebot.py && chmod +x /etc/init.d/telebot && chmod +x /root/Telebot-Radius/files/*
```
##### CHANGE BOT TOKEN
```
nano /root/Telebot-Radius/files/auth
```
===========================================================================
##### AUTO INSTALLER

```
cd /tmp && curl -sLko install https://raw.githubusercontent.com/Maizil41/Telebot-Radius/main/installer.sh && bash install
```
*
*
===========================================================================
##### AUTO RESTART
**COPY PASTE TO** `SCHEDULED TASKS`
```
*/30 * * * * service telebot restart
```
*
*
##### ENABLE SERVICE 

```
service telebot enable
```

##### START BOT 

```
service telebot start
```

##### RESTART BOT 

```
service telebot restart
```

##### STOP BOT 

```
service telebot stop
```
*
*
===========================================================================
