#!/usr/bin/bash
qterminal -e "mosquitto -c /home/krzysztof/Programy/Aplikacja/mosquitto/mosquitto.conf" &
cd /home/krzysztof/Programy/Aplikacja/www
qterminal -e "python3 -m http.server" &
cd /home/krzysztof/Programy/Aplikacja/baza
qterminal -e "python3 meter.py" &
qterminal -e "python3 storage.py" &
qterminal -e "python3 mcp2221.py" &
qterminal -e "python3 logger_db.py" &
cd /home/krzysztof/Programy/Aplikacja/bot_xmpp
qterminal -e "python3 xmpp_app_mqtt.py" &

