from time import sleep
import logging
import paho.mqtt.client as mqtt




BROKER='127.0.0.1'
PORT=9001

#topics
PREF='console/'
STATUS=PREF+'status'
CONTROL=PREF+'control'
DATA=PREF+'data'

#global variable
exit=False


#on message event function
def on_message(client, userdata, msg):
    logging.info(f'{msg.topic} {str(msg.payload.decode("utf-8"))}')
    



#-------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)

#mqtt client
client=mqtt.Client(client_id='console',clean_session=True,transport="websockets")
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

print('s u p e r')

subscribed=[]

while not exit:
    key=input('>>')

    keys=key.split()

    match keys[0]:
        case 's':  #subscribe
            client.subscribe(keys[1])
            subscribed.append(keys[1])
        
        case 'u':  #unsubscribe
            client.unsubscribe(keys[1])

        case 'p': #publish
            client.publish(keys[1],keys[2])
        
        case 'r': #unsubscribe everything
            for i in subscribed:
                client.unsubscribe(i)
            subscribed=[]

        case 'e': #exit
            exit=True 
            


#stop mqtt loop
client.loop_stop()





