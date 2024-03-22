import serial
import datetime
import logging
from time import sleep
import paho.mqtt.client as mqtt
import json

import byte_to_float
import utils

BROKER='127.0.0.1'
PORT=9001

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
    global exit
    json_payload=json.loads(str(msg.payload.decode("utf-8")))
    if (msg.topic==CONTROL):
        if ('command' in json_payload.keys()):
            #jest klucz 'command'
            if (json_payload['command']=='exit'):
                exit=True




#-------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)

#mqtt client
client=mqtt.Client(client_id='meter',clean_session=False,transport="websockets")
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
client.subscribe(CONTROL)

#rs485
connected=False

while not connected:
    #open serial port
    try:
        #open port
        port=serial.Serial('/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0',9600) 
    except:
        #error during opening port
        logging.error("Serial port open error: ttyUSB0")
        client.publish(STATUS,f'{utils.now()}: Serial port open error: ttyUSB0')
        sleep(10)
    else:
        connected=True
    
#port params
port.parity=serial.PARITY_EVEN
port.timeout=0.9

#read data from OR-WE_517 meter
#set previous time
previous_read_time=datetime.datetime.now()
while not exit:
    client.publish(STATUS,f'{utils.now()}: Meter running')
    #send queries for all type off data
    for query in QUERRIES:
        port.write(QUERRIES[query][0])

        #number of bytes from dict
        read=port.read(QUERRIES[query][1])

        #number of bytes from dict
        read_f=byte_to_float.b_to_f(read[3:7])

        
        #publish
        pub_valid=str(datetime.datetime.now()+2*INTERVAL).split('.')[0]  #how long data is valid, need this for storage
        data=json.dumps({'time':utils.now(),'value':round(read_f,2),'valid':pub_valid})
        client.publish(f'{DATA}/{query}',data)

        logging.info(f'{query:15} : {read_f:.2f}')
    
    time=datetime.datetime.now()
    #read after an interval
    while ((time-previous_read_time)<INTERVAL):
        #wait
        sleep(0.2)
        time=datetime.datetime.now()
    
    #previous time set to now
    previous_read_time=time
    

client.publish(STATUS,f'{utils.now()}: Meter stopped')   
#received exit command
#close rs485
port.close()

#stop mqtt loop
client.loop_stop()




