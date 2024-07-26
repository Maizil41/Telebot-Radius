# Telebot-Radius
 Telegram bot for daloradius billing

```
opkg update
```
```
opkg install git
```
```
opkg install jq
```
```
opkg install sysstat
```
```
opkg install git-http
```
```
opkg install python3
```
```
opkg install python3-venv
```
```
opkg install python3-pip
```
```
pip3 install python-telegram-bot
```
```
pip3 install python-filter
```
```
pip3 install pymysql
```

===========================================================================

```
git clone https://github.com/Maizil41/Telebot-Radius.git
```
```
mv /root/Telebot-Radius/files/telebot /etc/init.d/ && mv /root/Telebot-Radius/files/telebot.py /usr/bin/ && chmod +x /usr/bin/telebot.py && chmod +x /etc/init.d/telebot && chmod +x /root/Telebot-Radius/files/*
```
===========================================================================

##### AUTO RESTART
**COPAS TO** `SCHEDULED TASKS`
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
