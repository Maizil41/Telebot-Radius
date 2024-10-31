#!/bin/sh

CONFIG_FILE="/etc/config/telebot"
ENABLED=$(uci get telebot.@telebot[0].enabled)

if [ "$ENABLED" -eq 1 ]; then
    if pgrep -f "python3 /usr/bin/telebot.py" > /dev/null; then
        echo "Bot is already running"
    else
        python3 /usr/bin/telebot.py > /var/log/telebot.log 2>&1 &
        echo "Bot started"
    fi
else
    if pgrep -f "python3 /usr/bin/telebot.py" > /dev/null; then
        killall python3
        echo "Bot stopped"
    else
        echo "Bot is not running"
    fi
fi

/etc/telebot/status.sh
