import datetime
from time import sleep
import logging
import paho.mqtt.client as mqtt
import json
import queue
import sqlite3

import utils
import gather_data
from keys import *



DIR='/home/krzysztof/Pomiary/pomiar_'
DIR_POMIARY='/home/krzysztof/Pomiary/'

BROKER='127.0.0.1'
PORT=9001

#topics
PREF='storage/'
STATUS=PREF+'status'
CONTROL=PREF+'control'
DATA=PREF+'data'

INTERVAL=datetime.timedelta(minutes=1)

#global variable
exit=False

ceny={'koszty':{'G11':0.64,'T1':0.63,'T2':1.01,'T3':0.36}}

#on message event function
def on_message(client, userdata, msg):
    logging.info(f'STORAGE: received message: {msg.topic} {str(msg.payload.decode("utf-8"))}')
    global exit
    json_payload=json.loads(str(msg.payload.decode("utf-8")))
    #print(json_payload)
    
    if ('meter/data' in msg.topic) or ('mcp/data/temp_water' == msg.topic) or ('mcp/data/temp_outside' == msg.topic) or ('mcp/data/pressure' == msg.topic):
        client.queue.put(msg)
    


class Storage2:
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
    

    
    def _buffer_save(self):
        #save the data to the file

        #begining of log line: the date and time
        self.file_buf=f"insert into dane values ('{utils.now()}',"
        
        for self.kk in self.buffer:
            #compose the data line
            if self.buffer[self.kk]['valid']>=self.time:
                #data is still valid
                self.file_buf+=f'{self.buffer[self.kk]["value"]:.2f},'
            else:
                self.file_buf+=f'NULL,'
        self.file_buf=self.file_buf[:-1]+')' #remove last "," and add ")"

        #write data to db
        con=sqlite3.connect('/home/krzysztof/Pomiary/baza_pomiarow.db')
        cur=con.cursor()

        cur.execute(self.file_buf)
        con.commit()

        con.close()
        logging.info(f'SQL querry:{self.file_buf}')
            

    def add(self, msg):
        #adds a message of topic to buffer
        #remember msg topic
        self.topic=msg.topic
        #get value type from topic
        self.value_type=self.topic.split('/')[-1]
        #load payload as json
        self.payload=json.loads(msg.payload.decode('utf-8'))
        #get the message time
        self.msg_time=utils.str_to_date(self.payload['time'])
        #get the valid time
        #print('---------------',self.payload)
        self.msg_valid=utils.str_to_date(self.payload['valid'])

        #add to buffer
        self.buffer[self.value_type]['value']=self.payload['value']
        self.buffer[self.value_type]['valid']=self.msg_valid
        #self.buffer[self.value_type]['new']=True
        
    def check_interval(self):
        #checks if it is time to save data
        self.time=datetime.datetime.now()
        if (self.time-self.interval)>=self.previous_time:
            self.previous_time=self.time
            self._buffer_save()
                    
            


def generate_plot_data(json_payload):
    #get data from storage and prepare right data for type of plot
    match (json_payload['type']):
        case 'day_consumption':
            return day_consumption_data(json_payload['date_from'],json_payload['date_to'])
        case 'day_cost':
            return day_cost_data(json_payload['date_from'],json_payload['date_to'])
        case 'time_record':
            return time_record_data(json_payload['variable'],json_payload['date_time_from'],json_payload['date_time_to'])


def day_consumption_data(str_date_from,str_date_to):
    """string parameters, calculates sum of power consumption and min, average and max temperature of the day"""
    date_from=datetime.datetime.fromisoformat(str_date_from)
    date_to=datetime.datetime.fromisoformat(str_date_to)

    #pobranie danych z odpowiednich plików
    table=gather_data.gather(DIR_POMIARY,"pomiar_",date_from,date_to)
    zuzycie={}

    #brak danych z tego okresu
    if table=={}:
        return table

    #słownik ze zużyciem dla poszczególnych dni
    #iterujemy po kluczach
    #!!!!!!!!!!!!!!!dodać pobieranie informacji z poprzedniego dnia
    #obliczenie zużycia dziennego w strefach
    for dzien in table:
        #suma=table[dzien][-1]['sum']-table[dzien][0]['sum']
        #find first and last an hour, when T1, T2 and T3 are not '---'
        first=0
        last=-1
        while (table[dzien][first]['T1']=='---') or (table[dzien][first]['T2']=='---') or (table[dzien][first]['T3']=='---'):
            first+=1
            if first>len(table[dzien]):
                break
                #reached the end of the day
        while (table[dzien][last]['T1']=='---') or (table[dzien][last]['T2']=='---') or (table[dzien][last]['T3']=='---'):
            last-=1
            if last<(-len(table[dzien])):
                break
                #reached the begining of the day
        
        #is holiday, T3 during all the day
        if gather_data.is_holiday(dzien):
            T1=0.0
            T2=0.0
            T3=table[dzien][last]['T1']-table[dzien][first]['T1']+table[dzien][last]['T2']-table[dzien][first]['T2']+table[dzien][last]['T3']-table[dzien][first]['T3']
            #dodawanie wartości dziennego zużycia na potrzeby pie chart 
        else:
            T1=table[dzien][last]['T1']-table[dzien][first]['T1']
            T2=table[dzien][last]['T2']-table[dzien][first]['T2']
            T3=table[dzien][last]['T3']-table[dzien][first]['T3']

        #calculate min, average and max temperature

        T_min=0.0
        T_max=0.0
        T_sum=0.0
        T_av=0.0
        li=0
        first=True

        for measurement in table[dzien]:
            
            temp_value=measurement['temp_outside']
            if temp_value!='---':
                #there is a valid value
                li+=1
                T_sum+=temp_value
                
                if first:
                    first=False
                    T_min=temp_value
                    T_max=temp_value
                else:
                    #find the smallest value
                    if T_min>temp_value:
                        T_min=temp_value
                    #find the biggest value
                    if T_max<temp_value:
                        T_max=temp_value
        if li>0:
            T_av=T_sum/li
        
                

        #zuzycie[dzien]={'sum':round(suma,2),'T1':round(T1,2),'T2':round(T2,2),'T3':round(T3,2)}
        zuzycie[str(dzien)]={'T1':round(T1,2),'T2':round(T2,2),'T3':round(T3,2),'T_min':round(T_min,1),'T_av':round(T_av,1),'T_max':round(T_max,1),}

    return zuzycie
def day_cost_data(str_date_from,str_date_to):
    #calculate cost for each day and tariff

    date_from=datetime.datetime.fromisoformat(str_date_from)
    date_to=datetime.datetime.fromisoformat(str_date_to)

    #pobranie danych z odpowiednich plików
    table=gather_data.gather(DIR_POMIARY,"pomiar_",date_from,date_to)
    zuzycie={}

    #brak danych z tego okresu
    if table=={}:
        return table
    #dict with costs
    costs={}
    

    #słownik ze zużyciem dla poszczególnych dni
    #iterujemy po kluczach
    #!!!!!!!!!!!!!!!dodać pobieranie informacji z poprzedniego dnia
    #obliczenie zużycia dziennego w strefach 
    for dzien in table:
        #find first and last an hour, when T1, T2 and T3 are not '---'
        first=0
        last=-1
        while (table[dzien][first]['T1']=='---') or (table[dzien][first]['T2']=='---') or (table[dzien][first]['T3']=='---'):
            first+=1
            if first>len(table[dzien]):
                break
                #reached the end of the day
        while (table[dzien][last]['T1']=='---') or (table[dzien][last]['T2']=='---') or (table[dzien][last]['T3']=='---'):
            last-=1
            if last<(-len(table[dzien])):
                break
                #reached the begining of the day
                
        #is holiday, T3 during all the day
        meas={}
        if gather_data.is_holiday(dzien):
            meas['T1']=0.0
            meas['T2']=0.0
            meas['T3']=table[dzien][last]['T1']-table[dzien][first]['T1']+table[dzien][last]['T2']-table[dzien][first]['T2']+table[dzien][last]['T3']-table[dzien][first]['T3']
            #dodawanie wartości dziennego zużycia na potrzeby pie chart 
        else:
            meas['T1']=table[dzien][last]['T1']-table[dzien][first]['T1']
            meas['T2']=table[dzien][last]['T2']-table[dzien][first]['T2']
            meas['T3']=table[dzien][last]['T3']-table[dzien][first]['T3']

        costs[str(dzien)]={}
        #calculations for T1, T2 and T3
        costs[str(dzien)]['sum']=0.0
        for kk in ['T1','T2','T3']:
            tmp=meas[kk]*ceny['koszty'][kk]
            #add to overall day cost
            costs[str(dzien)]['sum']+=tmp
            costs[str(dzien)][kk]=round(tmp,2)

        costs[str(dzien)]['sum']=round(costs[str(dzien)]['sum'],2)
        costs[str(dzien)]['sumG11']=round((meas['T1']+meas['T2']+meas['T3'])*ceny['koszty']['G11'],2)
    
    return costs

def time_record_data(str_value,str_date_time_from,str_date_time_to):
    """returns power in time"""

    date_time_from=datetime.datetime.fromisoformat(str_date_time_from)
    date_time_to=datetime.datetime.fromisoformat(str_date_time_to)

    data=gather_data.gather_time(DIR_POMIARY,"pomiar_",date_time_from,date_time_to)
    #print(data)
    send_data={}
    for time in data:
        tmp=data[time][str_value]
        if tmp!='---':
            send_data[str(time)]=tmp
    
    return {'variable':str_value,'data':send_data}

#-------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)

#mqtt client
client=mqtt.Client(client_id='storage_db',clean_session=False,transport="websockets")
client.on_message=on_message

#add queue to client object
client.queue=queue.Queue()

#buffer object
#data_buf=Storage(INTERVAL)
data_buf=Storage2(INTERVAL)

connected=False

#try to connect until connected
while not connected:
    try:
        #try connecting
        client.connect(BROKER,PORT)
    except:
        logging.error(f'Unable to connect do broker {BROKER}:{PORT}')
        sleep(10)
    else:
        connected=True

#start mqtt loop
client.loop_start()
client.subscribe(CONTROL)
client.subscribe('meter/data/#')
client.subscribe('mcp/data/#')
#client.publish(STATUS,f'{utils.now()}: Storage running') 

while not exit:
    if not client.queue.empty():
    #print('tu')
    
        data_buf.add(client.queue.get())
    
    data_buf.check_interval()





#client.publish(STATUS,f'{utils.now()}: Storage stopped')   
#received exit command


#stop mqtt loop
client.loop_stop()






                    
                    
