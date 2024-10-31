#!/bin/sh
if pgrep -f "python3 /usr/bin/telebot.py" > /dev/null
then
    echo "Bot is running"
else
    echo "Bot is not running"
fi