import datetime
from time import sleep
import logging
import paho.mqtt.client as mqtt
import json
import queue

import utils
import gather_data


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
    if (msg.topic==CONTROL):
        if ('command' in json_payload.keys()):
            #jest klucz 'command'
            if (json_payload['command']=='exit'):
                exit=True
            elif (json_payload['command']=='get_data'):
                #generate data for plot
                logging.info(f'STORAGE:Plot data requested: {json_payload["type"]}')
                send_data=generate_plot_data(json_payload)
                #send data to proper web page
                client.publish(f'{DATA}/web/{json_payload["answer_to"]}',json.dumps({'data_type':f'{json_payload["type"]}','data':send_data}))
        
    elif ('meter/data' in msg.topic):
        client.queue.put(msg)
    



class Storage:
    def __init__(self,interval):
        self.buffer={"power_mom":0.0,
                     "power":0.0,
                     "power_T1":0.0,
                     "power_T2":0.0,
                     "power_T3":0.0}
        self.time=datetime.datetime.now()
        self.interval=interval
        self.previous_time=datetime.datetime.now()-self.interval
        #if buffer is being filled
        self.filling=False
    
    def _buffer_full(self):
        #check if buffer is full and ready to save
        for kk in self.buffer:
            if self.buffer[kk]==0.0:
                return False
        return True
    
    def _buffer_clear(self):
        #clear the buffer
        for kk in self.buffer:
            self.buffer[kk]=0.0
        #self.time=''
        #self.filling=False

    def _file_name(self):
    #return file name to save data
        teraz=datetime.datetime.now()
        return DIR+str(teraz.year)+'.'+str(teraz.month)

    def _buffer_save(self):
        #save the data to the file

        #beggining of log line: the date and time
        self.file_buf=self.time+';'

        #compose the data line
        for d in self.buffer:
            self.file_buf+=f'{self.buffer[d]:.2f};'
        self.file_buf+='\n'

        #write data to file
        with open(self._file_name(),'a') as file:
            file.write(self.file_buf)
            logging.info(f'Wrote {self.file_buf} to file')
            

    def add(self, msg):
        #adds a message of topic to buffer
        #remember msg topic
        self.topic=msg.topic
        #get value type from topic
        self.value_type=self.topic.split('/')[2]
        #load payload as json
        self.payload=json.loads(msg.payload.decode('utf-8'))
        #get the message time
        self.msg_time=utils.str_to_date(self.payload['time'])

        self.now=datetime.datetime.now()
        #check if it is time for next buffer
        #if (not self.filling) and (self.msg_time-self.previous_time>=self.interval):
        #    self._buffer_clear()
        #    self.filling=True
        #    #time for logging
        #    self.time=self.payload['time']
        #    self.previous_time=self.msg_time

        #if self.filling:
       # 	#no enough data in inerval time
        #	if (self.msg_time - self.previous_time>=self.intetrval):
        #	    self._buffer_clear()
        #    self.buffer[self.value_type]=self.payload['value']
        #    logging.info(f'Added to buffor: {self.value_type} - {self.payload["value"]}')
        #    if self._buffer_full():
        #        #time to save
        #        self._buffer_save()
        #        self.filling=False
                
                
        if (self.msg_time-self.previous_time>=self.interval):
            if (self.filling):
                logging.error("No enough data during interval")
            self._buffer_clear()
            self.filling=True
            #time for logging
            self.time=self.payload['time']
            self.previous_time=self.msg_time

        if self.filling:
            self.buffer[self.value_type]=self.payload['value']
            logging.info(f'Added to buffer: {self.value_type} - {self.payload["value"]}')
            if self._buffer_full():
                #time to save
                self._buffer_save()
                self.filling=False

def generate_plot_data(json_payload):
    #get data from storage and prepare right data for type of plot
    match (json_payload['type']):
        case 'day_consumption':
            return day_consumption_data(json_payload['date_from'],json_payload['date_to'])
        case 'day_cost':
            return day_cost_data(json_payload['date_from'],json_payload['date_to'])


def day_consumption_data(date_from,date_to):
    date_from=datetime.datetime.fromisoformat(date_from)
    date_to=datetime.datetime.fromisoformat(date_to)

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
        #is holiday, T3 during all the day
        if gather_data.is_holiday(dzien):
            T1=0.0
            T2=0.0
            T3=table[dzien][-1]['T1']-table[dzien][0]['T1']+table[dzien][-1]['T2']-table[dzien][0]['T2']+table[dzien][-1]['T3']-table[dzien][0]['T3']
            #dodawanie wartości dziennego zużycia na potrzeby pie chart 
        else:
            T1=table[dzien][-1]['T1']-table[dzien][0]['T1']
            T2=table[dzien][-1]['T2']-table[dzien][0]['T2']
            T3=table[dzien][-1]['T3']-table[dzien][0]['T3']


        #zuzycie[dzien]={'sum':round(suma,2),'T1':round(T1,2),'T2':round(T2,2),'T3':round(T3,2)}
        zuzycie[str(dzien)]={'T1':round(T1,2),'T2':round(T2,2),'T3':round(T3,2)}

    return zuzycie
def day_cost_data(date_from,date_to):
    #calculate cost for each day and tariff

    date_from=datetime.datetime.fromisoformat(date_from)
    date_to=datetime.datetime.fromisoformat(date_to)

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
        #is holiday, T3 during all the day
        meas={}
        if gather_data.is_holiday(dzien):
            meas['T1']=0.0
            meas['T2']=0.0
            meas['T3']=table[dzien][-1]['T1']-table[dzien][0]['T1']+table[dzien][-1]['T2']-table[dzien][0]['T2']+table[dzien][-1]['T3']-table[dzien][0]['T3']
            #dodawanie wartości dziennego zużycia na potrzeby pie chart 
        else:
            meas['T1']=table[dzien][-1]['T1']-table[dzien][0]['T1']
            meas['T2']=table[dzien][-1]['T2']-table[dzien][0]['T2']
            meas['T3']=table[dzien][-1]['T3']-table[dzien][0]['T3']

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

#-------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)

#mqtt client
client=mqtt.Client(client_id='storage',clean_session=False,transport="websockets")
client.on_message=on_message

#add queue to client object
client.queue=queue.Queue()

#buffer object
data_buf=Storage(INTERVAL)

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
client.publish(STATUS,f'{utils.now()}: Storage running') 

while not exit:
    if not client.queue.empty():
    #print('tu')
    
        data_buf.add(client.queue.get())





client.publish(STATUS,f'{utils.now()}: Storage stopped')   
#received exit command


#stop mqtt loop
client.loop_stop()






                    
                    


