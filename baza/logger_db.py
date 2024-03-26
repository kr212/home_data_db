import datetime
from time import sleep
import logging
import paho.mqtt.client as mqtt
import json
import queue
import sqlite3

import utils




DIR='/home/krzysztof/Pomiary/pomiar_'
DIR_POMIARY='/home/krzysztof/Pomiary/'

BROKER='127.0.0.1'
PORT=9001

#topics
PREF='logger/'
STATUS=PREF+'status'
CONTROL=PREF+'control'
DATA=PREF+'data'

#topics to save
TOPICS=['meter/data/power_mom','meter/data/power','meter/data/power_T1','meter/data/power_T2','meter/data/power_T3','mcp/data/temp_water','mcp/data/temp_outside','mcp/data/pressure']

INTERVAL=datetime.timedelta(minutes=1)

#global variable
exit=False


#on message event function
def on_message(client, userdata, msg):
    logging.debug(f"""{utils.color('blue')}Received message {utils.color()}: {msg.topic} {str(msg.payload.decode("utf-8"))}""")
    global exit
    json_payload=json.loads(str(msg.payload.decode("utf-8")))
    #print(json_payload)
    if (msg.topic==CONTROL):
        if ('command' in json_payload.keys()):
            #'command' key present
            if (json_payload['command']=='exit'):
                logging.info('Exit command received')
                exit=True
    elif msg.topic in TOPICS:
        client.queue.put(msg)
    


class DataLogger:
    def __init__(self,interval):
        #[data,new data added?]
        self.buffer={"power_mom":{'value':0.0,'valid':datetime.datetime(2000,1,1),'new':False},
                     "power":{'value':0.0,'valid':datetime.datetime(2000,1,1),'new':False},
                     "power_T1":{'value':0.0,'valid':datetime.datetime(2000,1,1),'new':False},
                     "power_T2":{'value':0.0,'valid':datetime.datetime(2000,1,1),'new':False},
                     "power_T3":{'value':0.0,'valid':datetime.datetime(2000,1,1),'new':False},
                     "temp_water":{'value':0.0,'valid':datetime.datetime(2000,1,1),'new':False},
                     "temp_outside":{'value':0.0,'valid':datetime.datetime(2000,1,1),'new':False},
                     "pressure":{'value':0.0,'valid':datetime.datetime(2000,1,1),'new':False}}
        #time when storage started
        self.time=datetime.datetime.now()
        self.interval=interval
        self.previous_time=self.time
        self.query_buffer=[]
    

    
    def _querry_compose(self):
        #compose querry and add it to the queue

        #begining of the sql querry 
        SQL_querry=f"INSERT INTO dane VALUES ('{utils.now()}',"
        
        for kk in self.buffer:
            #compose the SQL querry
            if self.buffer[kk]['valid']>=self.time:
                #data is still valid
                SQL_querry+=f'{self.buffer[kk]["value"]:.2f},'
            else:
                SQL_querry+=f'NULL,'
        SQL_querry=SQL_querry[:-1]+')' #remove last "," and add ")"

        self.query_buffer.append(SQL_querry)

    def _buffer_save(self):
        #write data to db
        con=sqlite3.connect('/home/krzysztof/Pomiary/baza_pomiarow.db',timeout=15)
        cur=con.cursor()
        
        try:
            while len(self.query_buffer)>0:

                que=self.query_buffer[0]

                cur.execute(que)
                con.commit()
                logging.info(f"{utils.color('green')}SQL querry {utils.color()}:{que}")
                self.query_buffer.pop(0)
        except:
            logging.warning(f"{utils.color('red')}SQL querry {utils.color()}:{que}\n{utils.color(bg='red')}Database busy{utils.color()}")
        con.close()
        
            

    def add(self, msg):
        #adds a message of topic to buffer
        #remember msg topic
        topic=msg.topic
        #get value type from topic
        value_type=topic.split('/')[-1]
        #load payload as json
        payload=json.loads(msg.payload.decode('utf-8'))
        #get the message time
        msg_time=utils.str_to_date(payload['time'])
        #get the valid time
        #print('---------------',self.payload)
        msg_valid=utils.str_to_date(payload['valid'])

        #add to buffer
        self.buffer[value_type]['value']=payload['value']
        self.buffer[value_type]['valid']=msg_valid
        #self.buffer[self.value_type]['new']=True
        
    def check_interval(self):
        #checks if it is time to save data
        self.time=datetime.datetime.now()
        if (self.time-self.interval)>=self.previous_time:
            self.previous_time=self.time
            self._querry_compose()   #compose queries and save to buffer, in case the database is busy remaining querries will be executed during the next save process
            self._buffer_save()
                    



#-------------------------------------------------------------------
logging.basicConfig(format='LOGGER::%(levelname)s %(asctime)s : %(message)s\n',level=logging.DEBUG)

#mqtt client
client=mqtt.Client(client_id='logger',clean_session=False,transport="websockets")
client.on_message=on_message

#add queue to client object
client.queue=queue.Queue()

#buffer object
#data_buf=Storage(INTERVAL)
data_buf=DataLogger(INTERVAL)

connected=False

#try to connect until connected
while not connected:
    try:
        #try connecting
        client.connect(BROKER,PORT)
    except:
        logging.error(f'Unable to connect to broker {BROKER}:{PORT}')
        sleep(10)
    else:
        connected=True

#start mqtt loop
client.loop_start()
client.subscribe(CONTROL)
client.subscribe('meter/data/#')
client.subscribe('mcp/data/#')
client.publish(STATUS,f'{utils.now()}: Logger running') 

while not exit:
    if not client.queue.empty():
    #print('tu')
    
        data_buf.add(client.queue.get())
    
    data_buf.check_interval()





client.publish(STATUS,f'{utils.now()}: Logger stopped')   
#received exit command


#stop mqtt loop
client.loop_stop()






                    
                    
