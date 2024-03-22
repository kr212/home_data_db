import datetime
import logging
from time import sleep
import paho.mqtt.client as mqtt
import json
import EasyMCP2221

import byte_to_float
import utils
import bmp280
import aht20

BROKER='127.0.0.1'
PORT=9001

#topics
PREF='mcp/'
STATUS=PREF+'status'
CONTROL=PREF+'control'
DATA=PREF+'data'


#interval between reads
INTERVAL=datetime.timedelta(minutes=1)
#INTERVAL=datetime.timedelta(seconds=5)
#hom many times read the analog input
MEASUREMENTS=50

#global variable
exit=False

#elevation
elev_zlochowice=266 #m n.p.m.


#on message event function
def on_message(client, userdata, msg):
    logging.info(f'{msg.topic} {str(msg.payload.decode("utf-8"))}')
    global exit
    json_payload=json.loads(str(msg.payload.decode("utf-8")))
    if (msg.topic==CONTROL):
        if ('command' in json_payload.keys()):
            #jest klucz 'command'
            if (json_payload['command']=='exit'):
                exit=True

#some helpful functions
def adc_to_volt(adc,ref=2.048):
    #converts adc value to voltage
    return adc/1023*ref

def volt_to_temp_tmp(volt):
    #converts voltage to temp for tmp36gt9z sensor
    return 100.0*volt-50
    
def volt_to_temp_lm35(volt):
	#converts voltage to temp for lm35dz sensor
	return 100.0*volt+2



#-------------------------------------------------------------------
#logging.basicConfig(format='MCP2221.py::%(levelname)-%(asctime)s-%(message)s',datefmt='%d.%m.%Y %H:%M:%S', level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
#mqtt client
client=mqtt.Client(client_id='mcp',clean_session=False,transport="websockets")
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


connected=False

#try to connect until connected
while not connected:
    try:
        board=EasyMCP2221.Device()
    except RuntimeError:
        logging.error(f'Error while opening MCP2221 device')
        client.publish(STATUS,f'{utils.now()}: Error while opening MCP2221 device')
        sleep(10)
    else:
        connected=True
# logging.info('Reset')
# board.reset()
# sleep(10)
# logging.info('Reset done')

#connect to bmp280 sensor by I2C
bmp=board.I2C_Slave(0x76)
outside_sensor=bmp280.BMP280(bmp)

#connect to aht20 sensor by I2C
aht=board.I2C_Slave(0x38)
inside_sensor=aht20.AHT20(aht)

#board.debug_messages=True

    


#read data from MCP2221
#set previous time
previous_read_time=datetime.datetime.now()
while not exit:
    client.publish(STATUS,f'{utils.now()}: MCP running')
    #read analog data
    result=0
    for _ in range(MEASUREMENTS):
        tmp=board.ADC_read()
        result+=tmp[2]  #gpio3 as adc
        #print(f'ADC_read={tmp[2]}')
    
    data={}
    data['temp_water']=round(volt_to_temp_lm35(adc_to_volt(result/MEASUREMENTS)),2)
    
    data['temp_outside'], data['pressure_abs']=outside_sensor.read()     #tt.tt ppp.p
    
    data['pressure']=round(utils.press_sea_level(data['pressure_abs'],data['temp_outside'],elev_zlochowice),1)

    data['temp_inside'], data['humidity_inside']=inside_sensor.read()   #tt.t  hhhh.h

    #publish data
    pub_time=utils.now()
    pub_valid=str(datetime.datetime.now()+2*INTERVAL).split('.')[0]  #how long data is valid, need this for storage
    for names in data:
        #string=json.dumps({'time':utils.now(),'value':data[names]})
        string=json.dumps({'time':pub_time,'value':data[names],'valid':pub_valid})
        client.publish(f'{DATA}/{names}',string,retain=True)
        logging.info(f'Published ({names}): {string}')

    
    time=datetime.datetime.now()
    #read after an interval
    while ((time-previous_read_time)<INTERVAL) and (not exit):
        #wait
        sleep(1)
        time=datetime.datetime.now()
    
    #previous time set to now
    previous_read_time=time
    

client.publish(STATUS,f'{utils.now()}: MCP stopped')   
#received exit command


#stop mqtt loop
client.loop_stop()


