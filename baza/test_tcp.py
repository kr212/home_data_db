import serial
import datetime
import logging
from time import sleep
import paho.mqtt.client as mqtt
import json

import byte_to_float
import utils

BROKER='127.0.0.1'
PORT=1883

#topics
PREF='meter/'
STATUS=PREF+'status'
CONTROL=PREF+'control'
DATA=PREF+'data'

QUERRIES={

"power_mom":  [serial.to_bytes([0x01,0x03,0x00,0x1C,0x00,0x02,0x05,0xCD]),9],
"power":   [serial.to_bytes([0x01,0x03,0x01,0x00,0x00,0x02,0xC5,0xF7]),9],
"power_T1":[serial.to_bytes([0x01,0x03,0x01,0x30,0x00,0x02,0xC5,0xF8]),9],
"power_T2":[serial.to_bytes([0x01,0x03,0x01,0x3C,0x00,0x02,0x05,0xFB]),9],
"power_T3":[serial.to_bytes([0x01,0x03,0x01,0x48,0x00,0x02,0x45,0xE1]),9]}

#interval between reads
INTERVAL=datetime.timedelta(seconds=2)

#global variable
exit=False


#on message event function
def on_message(client, userdata, msg):
    print(f'{msg.topic} {str(msg.payload.decode("utf-8"))}')
    




#-------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)

#mqtt client
client=mqtt.Client()
client.on_message=on_message

connected=False

#try to connect until connected
while not connected:
    try:
        #try connecting
        client.connect(BROKER,port=PORT)
    except:
        logging.error(f'Unable to connect do broker {BROKER}:{PORT}')
        sleep(10)
    else:
        connected=True

#start mqtt loop
client.loop_start()
client.subscribe("test/#")

while True:
	pass

#stop mqtt loop
client.loop_stop()




