from sleekxmpp import ClientXMPP
from time import sleep
import datetime
import suntime
import logging
import paho.mqtt.client as mqtt
import json
import utils

BROKER='127.0.0.1'
PORT=9001

#topics
PREF='xmpp/'
STATUS=PREF+'status'
CONTROL=PREF+'control'
DATA=PREF+'data'



server_jid='st_dom@jabber.sytes24.pl'
server_pwd='st_dom_123'

#channels
#sunrise and sundown
sun_channel=[
    {'to':'kst@jabber.sytes24.pl','when':datetime.datetime(year=2024,month=1,day=1,hour=9,minute=0),'lat':50.915,'long':18.817778,'name':'Złochowice'}
]

#MQTT-----------------------------------------------------------------------------
#MQTT on message event function
def on_message(client, userdata, msg):
    logging.info(f'XMPP::{msg.topic} {str(msg.payload.decode("utf-8"))}')
    global work
    json_payload=json.loads(str(msg.payload.decode("utf-8")))
    if (msg.topic==CONTROL):
        if ('command' in json_payload.keys()):
            #jest klucz 'command'
            if (json_payload['command']=='exit'):
                work=False

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
    """checks if there is something to send in his channel and appends the send list"""
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


#program start
logging.basicConfig(level=logging.INFO)

#XMPP start----------------------------------------------------------------------------
work=True

xmpp=SendMsg(server_jid,server_pwd)
xmpp.connect()

xmpp.register_plugin('xep_0030')
xmpp.register_plugin('xep_0199')
xmpp.add_event_handler('message',got_message)
xmpp.process(block=False)


#MQTT start----------------------------------------------------------------------------
client=mqtt.Client(client_id='xmpp',clean_session=False,transport="websockets")
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



before=datetime.datetime.now()-datetime.timedelta(minutes=1)

print('BOT XMPP')

while work:
    client.publish(STATUS,f'{utils.now()}: XMPP BOT running')
    now=datetime.datetime.now()
    if now.minute==before.minute:
        sleep(1)
        continue

    before=now
    send_queue=[]
    sun_channel_process(send_queue)

    #send all data
    for data in send_queue:
        xmpp.send_message(mto=data[0],mbody=data[1],mtype='chat')
        logging.info(f'XMPP::{now}::Sent to {data[0]} a message: {data[1]}')
    #print('tic')
    #sleep(60)
    
    

client.publish(STATUS,f'{utils.now()}: XMPP BOT stopped')   
#received exit command


#stop mqtt loop
client.loop_stop()

quit()