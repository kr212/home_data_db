# home_data_db
Home data aquisition with sqlite database.
Repository contains modules that are used in my home data aquisition system to store info from ORNO OR-WE-517 energy meter and several other sensors.

## Hardaware
The following devices are used in this project:
- ORNO OR-WE-517 - energy meter with Modbus interface
- MCP2221a USB to GPIO breakout module - to use I2C AHT and BMP sensors
- AHT20 temperature and humidity sensor
- BMP280 temperature and pressure sensor
- USB to RS485 converter

## How does it work
The application consists of several modules that send data to the MQTT broker. Each module is responsible for different task.
Main modules are:
- /baza/mcp2221.py - communicates with MCP2221 board and gets data from AHT20 and BMP280 sensors, sends data to MQTT broker
- /baza/meter.py - communicates with OR-WE-517 meter using **USB to RS485** conerter, sends data to MQTT broker
- /baza/storage.py - gets data from MQTT broker and saves temperature and power related info to text files, also answers requests for data (used by web hmi and xmpp bot), will be replaced by sqlite3 database (see logger.py)
- /baza/logger.py - gets data from MQTT broker and puts it into sqlite3 database
- /baza/orno.py - module for ORNO OR-WE-517 energy meter

- /bot_xmpp/xmpp_app_mqtt.py - automated statistic sending using xmpp protocol

- /www/ - simple web hmi for vieving stored data, when using sqlite3 may be replaced by Grafana, data requests are send throug mqtt to storage.py module

## Python dependencies:
* pyserial
* paho mqtt

## Additional info
Project is under develophent, hence there may be a lot of not used code inside each module.
