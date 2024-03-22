from sleekxmpp import ClientXMPP
from time import sleep
import datetime
import suntime
import logging
import paho.mqtt.client as mqtt
import json

import sys

#need to import "utils" from different directory
sys.path.insert(0,'../baza')
import utils

BROKER='127.0.0.1'
PORT=9001

#topics
PREF='xmpp/'
STATUS=PREF+'status'
CONTROL=PREF+'control'
DATA=PREF+'data'

#read user ids and passwords from file for github privacy ;)
file=open('passwd','r')

server_jid=file.readline().rstrip()
server_pwd=file.readline().rstrip()
recipient=file.readline().rstrip()

file.close()

#channels
#sunrise and sundown
sun_channel=[
    {'to':recipient,'when':datetime.datetime(year=2024,month=1,day=1,hour=9,minute=0),'lat':50.915,'long':18.817778,'name':'Złochowice'}
]

power_channel=[
    {'to':recipient,'when':datetime.datetime(year=2024,month=1,day=1,hour=9,minute=0)}
]

#MQTT-----------------------------------------------------------------------------
#MQTT on message event function
def on_message(client, userdata, msg):
    logging.info(f'{utils.color("blue")}Received {utils.color()}{msg.topic} {str(msg.payload.decode("utf-8"))}')
    global work
    json_payload=json.loads(str(msg.payload.decode("utf-8")))
    if (msg.topic==CONTROL):
        if ('command' in json_payload.keys()):
            #jest klucz 'command'
            if (json_payload['command']=='exit'):
                work=False
    elif ('storage/data/xmpp/' in msg.topic):
        #got power usage from last day
        if (json_payload['data_type']=='day_consumption') and ('data' in json_payload.keys()):
            #valid key in dictionary
            key=list(json_payload['data'].keys())[0]
            #print(key)
            #key=json_payload['data'][keys[0]]
            day=datetime.datetime.fromisoformat(key)
            recipient=msg.topic.split('/')[-1]   #after last'/' there is a user name
            T1=json_payload['data'][key]['T1']
            T2=json_payload['data'][key]['T2']
            T3=json_payload['data'][key]['T3']
            p_sum=T1+T2+T3
            T_min=json_payload['data'][key]['T_min']
            T_av=json_payload['data'][key]['T_av']
            T_max=json_payload['data'][key]['T_max']
            client.send_queue.append([recipient,f'Zużycie energii z dnia {day.strftime(f"%d.%m.%Y")} [kWh]:\nT1: {T1}\nT2: {T2}\nT3: {T3}\nSuma: {p_sum:.2f}\nTemperatura na zewnątrz [°C]:\nMin: {T_min}\nŚrednia: {T_av}\nMax: {T_max}'])
            #print('tu')





#XMPP-----------------------------------------------------------------------------
class SendMsg(ClientXMPP):

    def __init__(self, jid, password):
        super(SendMsg, self).__init__(jid, password)

        self.add_event_handler('session_start', self.start)

    def start(self, event):
        self.send_presence()

#XMPP on message event function
def got_message(msg):
    if msg['type'] in ('chat','normal'):
        print(msg['body'])
        if msg['body'] in ('stop','Stop'):
            global work
            work=False
            quit()

#sun time-------------------------------------------------------------------------
def get_day_length_string(delta):
    """returns hours and minutes only from timedelta string"""
    delta_str=str(delta)
    # #find first occurence of ':'
    # text=delta_str[:delta_str.find(':')]+'g '+
    # return delta_str[:delta_str.find(':',tmp+1)]
    return delta_str.split(':')[0]+'g '+delta_str.split(':')[1]+'min'

def sun_channel_process(send_list,debug=False):
    """checks if there is something to send in this channel and appends the send list"""
    now=datetime.datetime.now()

    for members in sun_channel:
        if ((now.hour==members['when'].hour) and (now.minute==members['when'].minute)) or debug:
            sun=suntime.Sun(members['lat'],members['long'])
            sunrise=sun.get_local_sunrise_time()
            sunset=sun.get_local_sunset_time()
            day_length=sunset-sunrise
            #print(day_length)
            day_length_str=get_day_length_string(day_length)
            send_list.append([members['to'],f'Wschód i zachód słońca dla {members["name"]}: {sunrise.strftime("%H:%M")} - {sunset.strftime("%H:%M")}\nDługośc dnia: {day_length_str}'])

def power_channel_process(client,debug=False):
    """checks if there is something to send in this channel and appends the send list"""
    now=datetime.datetime.now()
    one_day=datetime.timedelta(days=1)

    for members in power_channel:
        if ((now.hour==members['when'].hour) and (now.minute==members['when'].minute)) or debug:
            #send data request - valid for only one user
            client.publish('storage/control',json.dumps({'command':'get_data','type':'day_consumption','date_from':str(now-one_day),'date_to':str(now-one_day),'answer_to':'xmpp/'+members['to']}))


#program start
logging.basicConfig(format='XMPP BOT::%(levelname)s %(asctime)s : %(message)s\n',level=logging.INFO)

#XMPP start----------------------------------------------------------------------------
work=True

xmpp=SendMsg(server_jid,server_pwd)
xmpp.connect()

xmpp.register_plugin('xep_0030')
xmpp.register_plugin('xep_0199')
xmpp.add_event_handler('message',got_message)
xmpp.process(block=False)


#MQTT start----------------------------------------------------------------------------
client_MQTT=mqtt.Client(client_id='xmpp',clean_session=False,transport="websockets")
client_MQTT.on_message=on_message
#add a send buffer to client - useful to transfer data from inside the on_messege function
client_MQTT.send_queue=[]
    
connected=False

#try to connect until connected
while not connected:
    try:
        #try connecting
        client_MQTT.connect(BROKER,port=PORT)
    except:
        logging.error(f'Unable to connect do broker {BROKER}:{PORT}')
        sleep(10)
    else:
        connected=True

#start mqtt loop
client_MQTT.loop_start()
client_MQTT.subscribe(CONTROL)
client_MQTT.subscribe('storage/data/xmpp/#')



before=datetime.datetime.now()-datetime.timedelta(minutes=1)

print('BOT XMPP')

send_queue=[]

while work:
    client_MQTT.publish(STATUS,f'{utils.now()}: XMPP BOT running')

    #send all data if there is any
    for send in (send_queue,client_MQTT.send_queue):
        # for data in range(len(send)):
        #     xmpp.send_message(mto=data[0],mbody=data[1],mtype='chat')
        #     logging.info(f'XMPP::{now}::Sent to {data[0]} a message: {data[1]}')
        while len(send)>0:
            data=send.pop()
            xmpp.send_message(mto=data[0],mbody=data[1],mtype='chat')
            logging.info(f'{utils.color("green")}Sent to {data[0]} a message{utils.color()}: {utils.color("yellow")}{data[1]}{utils.color()}')
    
    sleep(1)
    
    now=datetime.datetime.now()
    if now.minute==before.minute:   
        continue

    before=now
    
    #client.send_queue=[]
    sun_channel_process(send_queue)
    power_channel_process(client_MQTT)

    
    #print('tic')
    #sleep(60)
    
    

client_MQTT.publish(STATUS,f'{utils.now()}: XMPP BOT stopped')   
#received exit command


#stop mqtt loop
client_MQTT.loop_stop()

quit()
