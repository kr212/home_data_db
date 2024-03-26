import serial
import datetime
import logging
from time import sleep
import paho.mqtt.client as mqtt
import json

import byte_to_float
import utils
import orno

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

#summer and winter ivtervals for G13 tariff in Poland
SUMMER_INTERVAL=[(datetime.time(0,0),3),(datetime.time(7,0),1),(datetime.time(13,0),3),(datetime.time(19,0),2),(datetime.time(22,0),3)]
WINTER_INTERVAL=[(datetime.time(0,0),3),(datetime.time(7,0),1),(datetime.time(13,0),3),(datetime.time(16,0),2),(datetime.time(21,0),3)]
HOLIDAY_INTERVAL=[(datetime.time(0,0),3)]
SUMMER_START=datetime.date(2000,4,1)
WINTER_START=datetime.date(2000,10,1)
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
logging.basicConfig(format='METER::%(levelname)s %(asctime)s : %(message)s',level=logging.DEBUG)

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
        logging.error(f'Unable to connect to the broker {BROKER}:{PORT}')
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

#create meter object
meter=orno.Meter(port,1)
reg_tmp=meter.get_reg_names('work')

#create aliases dictionary, for backward compatibility (many other scripts uses old names)
registers={}
for reg in reg_tmp:
    registers[reg]=reg

registers['Total Active Power']='power_mom'
registers['Total Active Energy']='power'
registers['T1 Total Active Energy']='power_T1'
registers['T2 Total Active Energy']='power_T2'
registers['T3 Total Active Energy']='power_T3'


lines=len(registers.keys())

logging.info(f'Time updated : {utils.color("yellow")}{meter.sync_time()}{utils.color()}')


#check the holiday at startup
tim=datetime.datetime.now()
now=tim.date()

if utils.is_holiday(now):
    summer=datetime.date(now.year,SUMMER_START.month,SUMMER_START.day)
    winter=datetime.date(now.year,WINTER_START.month,WINTER_START.day)

    if (now>=summer and now<winter):
        int_to_change=1
    else:
        int_to_change=2

    holiday=tim.time()+datetime.timedelta(minutes=1)
    meter.set_interval(int_to_change,[(holiday,3)])
    set_in_meter='hol'
    logging.info('Set holiday tariff in meter')
else:
    meter.set_interval(1,SUMMER_INTERVAL)
    meter.set_interval(2,WINTER_INTERVAL)
    set_in_meter='ord'
    logging.info('Set standard tariff in meter')


#read data from OR-WE_517 meter
#set previous time
previous_read_time=datetime.datetime.now()
#was the time in the meter checked?
time_checked=False
minute_of_time_check=1
holiday_checked=False


#MAIN LOOP-----------------------------------------------------------------
while not exit:
    client.publish(STATUS,f'{utils.now()}: Meter running')
    #send queries for all type off data
    for query in registers:
        read_f=meter.read(query)

        
        #publish
        pub_valid=str(datetime.datetime.now()+2*INTERVAL).split('.')[0]  #how long data is valid, need this for storage
        data=json.dumps({'time':utils.now(),'value':round(read_f,2),'valid':pub_valid})
        #is an alias for topic name?
        client.publish(f'{DATA}/{registers[query]}',data)

        logging.info(f"Published: {utils.color('green')}{registers[query]:25} : {utils.color('blue')}{read_f:.2f}{utils.color()} ")
        
    

    time=datetime.datetime.now()
    #check time inside the meter every 1 minute past an hour
    if (time.minute==minute_of_time_check) and (not time_checked):
        logging.info(f'Time updated : {utils.color("yellow")}{meter.sync_time()}{utils.color()}')
        time_checked=True
    elif (time.minute!=minute_of_time_check):
        time_checked=False


    #check if it is a holiday day and change interval in the meter, always at 01:05
    if ((time.minute==5) and (time.hour==1)) and (not holiday_checked):
        holiday_checked=True
        logging.info('Holiday check')
        if (utils.is_holiday(time)) and (set_in_meter=='ord'):
            summer=datetime.date(time.year,SUMMER_START.month,SUMMER_START.day)
            winter=datetime.date(time.year,WINTER_START.month,WINTER_START.day)

            if (time.date()>=summer and time.date()<winter):
                int_to_change=1
            else:
                int_to_change=2

            holiday=time.time()+datetime.timedelta(minutes=1)
            meter.set_interval(int_to_change,[(holiday,3)])
            set_in_meter='hol'
            logging.info('Set holiday tariff in meter')
        elif (not utils.is_holiday(time)) and (set_in_meter=='hol'):
            meter.set_interval(1,SUMMER_INTERVAL)
            meter.set_interval(2,WINTER_INTERVAL)
            set_in_meter='ord'
            logging.info('Set standard tariff in meter')
    elif (time.minute!=5) or (time.hour!=1):
        holiday_checked=False
        
    #print(meter.get_interval(1))
    #print(meter.get_interval(2))
    #print(meter.get_zone())

    #time update
    time=datetime.datetime.now()
    #does the time between data reeds is to short?
    cycle_too_short=True
    #read after an interval
    while ((time-previous_read_time)<INTERVAL):
        #there was at least 1 loop execution
        cycle_too_short=False
        #print('czekam')
        #wait
        sleep(0.1)
        time=datetime.datetime.now()
    if cycle_too_short:
        client.publish(STATUS,f'{utils.now()}: Cycle too short')
        logging.warning(f"{utils.color(bg='red')}Cycle too short!{utils.color()}")
    #previous time set to now
    previous_read_time=time
    

client.publish(STATUS,f'{utils.now()}: Meter stopped')   
#received exit command
#close rs485
port.close()

#stop mqtt loop
client.loop_stop()




