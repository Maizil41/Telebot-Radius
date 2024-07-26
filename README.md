# Telebot-Radius
 Telegram bot for daloradius billing
======================= Proses installasi Telebot-Radius =======================

```
opkg update
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

==============================================================================

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
==============================================================================
