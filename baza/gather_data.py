import os
import glob
import datetime as dt
from keys import *
import sqlite3
import time as time_meassure
from utils import is_holiday

# holidays_const=[dt.datetime(2000,1,1),dt.datetime(2000,1,6),dt.datetime(2000,5,1),dt.datetime(2000,5,3),dt.datetime(2000,8,15),dt.datetime(2000,11,1),dt.datetime(2000,11,11),dt.datetime(2000,12,25),dt.datetime(2000,12,26)]
# holidays_easter=[dt.datetime(2023,4,10),dt.datetime(2024,4,1),dt.datetime(2025,4,21)]
# holidays_bc=[dt.datetime(2023,6,8),dt.datetime(2024,5,30),dt.datetime(2025,6,19)]

#keys=["time","power","sum","T1","T2","T3","temp_water","temp_outside","pressure"]

def gather(dir,file, date_from=0,date_to=0):
    #takes data from files "pomiar_yyyy.mm"
    #date_from, date_to - time interval, have to be datetime type
    #returns: {day1: [time,power kW, summarized power consumption kWh, T1 power consumpion kWh, , T2 power consumpion kWh, , T3 power consumpion kWh],
    #          "day2": [time,power kW, summarized power consumption kWh, T1 power consumpion kWh, , T2 power consumpion kWh, , T3 power consumpion kWh],
    #           .
    #           .
    #           .}
    # date_from=0 - data from the beggining
    # date_to=0 - data up to now
    # files for example: '/home/krzysztof/Pomiary/pomiar_'+'yyyy.mm'
    start=time_meassure.time()
    if (date_from==0):
        date_from=dt.datetime(2022,10,1,0,0,0)
    if (date_to==0):
        date_to=dt.datetime.now()
    if date_from>date_to:
        return {}

    #delta=dt.timedelta(days=1)

    #have to find all the files
    found_files=glob.glob(os.path.join(dir,file+'*')) #list of all files
    print(found_files)
    if len(found_files)==0:
        return {}  #no files found
    
    found_files.sort()
   
    
    #begining of file list
    list_start=0
    #remove the begining of the list up to valid start date
    #find_str=str(date_from.year)+'.'+str(date_from.month)
    find_str=str(date_from.year)+'.'+f'{date_from.month:02}'

    for i in range(len(found_files)):
        if found_files[i].find(find_str)!=-1:
            list_start=i
            break
    
    #ending of file list
    list_end=len(found_files) 

    #remove the ending of the list from valid end date
    #find_str=str(date_to.year)+'.'+str(date_to.month)
    find_str=str(date_to.year)+'.'+f'{date_to.month:02}'
    for i in range(list_start,len(found_files)):
        if found_files[i].find(find_str)!=-1:
            list_end=i+1
            break       
    
    #cutting the beggining and the end
    found_files=found_files[list_start:list_end]

    #open all files from list and add them to dictionary
    table={}
    for files in found_files:
        #oczekuje na zwolnienie piku
        while os.path.exists(files+'.lck'):
            pass
        
        #blokuje plik
        plik_lck=open(files+'.lck','w')
        plik_lck.close()

        file=open(files,'r',encoding="utf-8")

        for date in file:
            data_spl=date.split(';')[:-1]  #throw away \n at the end
            date_time=dt.datetime.fromisoformat(data_spl[0])
            date=date_time.date()
            time=date_time.time()
            if not date in table.keys():
                table[date]=[]
            tmp={'time':time}
            #print(f'GATHER {data_spl}')
            #table[date].append({'time':time,'power':float(data_spl[1]),'sum':float(data_spl[2]),'T1':float(data_spl[3]),'T2':float(data_spl[4]),'T3':float(data_spl[5])})
            for kk in range(1,len(keys)):
                #from 1 because time is already added
                #print(kk)
                try:
                #can be '---'
                    tmp[keys[kk]]=float(data_spl[kk])
                except:
                    tmp[keys[kk]]='---'
            table[date].append(tmp)
        
        file.close()

        #usuwam blokadę
        os.remove(files+'.lck')

    #remove keys outside the time interval 
    keys_to_remove=[]   
    
    for k in table.keys():
        if (k<date_from.date()):
            keys_to_remove.append(k)
    
    for k in table.keys():
        if (k>date_to.date()):
            keys_to_remove.append(k)
    for kk in keys_to_remove:
        del table[kk]
    end=time_meassure.time()
    print(f'Gather took: {end-start}s')
    return table


# def is_holiday(day):
# #check if date is a holiday
#     for d in holidays_const:
#         if (d.month==day.month) and (d.day==day.day):
#             return True
#     if (day in holidays_bc) or (day in holidays_easter):
#         return True
#     return False

def gather_time(dir,file, date_time_from=0,date_time_to=0):
    #takes data from files "pomiar_yyyy.mm"
    #date_time_from, date_time_to - time interval, have to be datetime type
    #returns: {"date_time": [power kW, temp_water,temp_outside,pressure],
    #          "date_time": [power kW, temp_water,temp_outside,pressure],
    #           .
    #           .
    #           .}
    # date_time_from=0 - data from the beggining
    # date_time_to=0 - data up to now
    # files for example: '/home/krzysztof/Pomiary/pomiar_'+'yyyy.mm'

    if (date_time_from==0):
        date_time_from=dt.datetime(2022,10,1,0,0,0)
    if (date_time_to==0):
        date_time_to=dt.datetime.now()
    if date_time_from>date_time_to:
        return {}

    table=gather(dir,file,date_time_from,date_time_to)

    table_time={}

      
    
    
    #itereate through all keys and table positions
    for k in table.keys():
        for m in table[k]:
            #create datetime from date(key) and time(key)
            date_time=dt.datetime(k.year,k.month,k.day,m['time'].hour,m['time'].minute,m['time'].second)
            if (date_time>=date_time_from) and (date_time<=date_time_to):
                #copy data to new table-protect when key is not present!!!!!!!!!!!!
                table_time[date_time]={keys[1]:m[keys[1]],keys[6]:m[keys[6]],keys[7]:m[keys[7]],keys[8]:m[keys[8]]}

    
    return table_time
    #return:
    #{time_data1:{'power':xx,'temp':xx..},
    #{time_data2:{'power':xx,'temp':xx..}}


def get(base, date_from_p=0,date_to_p=0,memory=False):
    #takes data from sqlite database
    #date_from, date_to - time interval, have to be datetime type
    #returns: {day1: [
    #           {time,power kW, summarized power consumption kWh, T1 power consumpion kWh, , T2 power consumpion kWh, , T3 power consumpion kWh},
    #           {...}
    #               ],
    #          day2: [{time,power kW, summarized power consumption kWh, T1 power consumpion kWh, , T2 power consumpion kWh, , T3 power consumpion kWh},{...}],
    #           .
    #           .
    #           .}
    # date_from=0 - data from the beggining
    # date_to=0 - data up to now
    #base - full base path
    start=time_meassure.time()
    #copy in case of changing
    date_from=date_from_p
    date_to=date_to_p
    if (date_from==0):
        date_from=dt.datetime(2022,10,1,0,0,0)
    if (date_to==0):
        date_to=dt.datetime.now()
    if date_from>date_to:
        tmp=date_to
        date_to=date_from
        date_from=tmp

    #delta=dt.timedelta(days=1)
    #current_date=date_from

    #table with data
    table={}

    #get data from db
    #con=sqlite3.connect('/home/krzysztof/Pomiary/baza_pomiarow.db')
    try:
        if memory:
            con_a=sqlite3.connect(base)
        else:
            con=sqlite3.connect(base)
    except:
        return table
    
    #copy database to the memory
    if memory:
        con=sqlite3.connect(':memory:')
        con_a.backup(con)
        con_a.close()
    
    cur=con.cursor()

    #iterate through all dates
    # while current_date<=date_to:
    #     #get data for each day
    #     print('pik')
    #     SQL_querry=f'SELECT * FROM dane WHERE date(date) = date("{str(current_date.date())}") ORDER BY datetime(date) ASC'
    #     #SQL_querry=f'SELECT * FROM dane WHERE date = "{str(current_date.date())}"'
    #     #SQL_querry=f'SELECT * FROM dane WHERE date(date) = date("{str(current_date.date())}")'
        
    #     tmp=cur.execute(SQL_querry)

    #     tmp=tmp.fetchall()
    #     print('pyk')
    #     #tmp=[(datetime, power_mom ...),(datetime, power_mom ...)...]
    #     if len(tmp)>0:
    #         #datetim=dt.datetime.fromisoformat(tmp[0][0])
    #         #create date key in table
    #         #table[datetim.date()]=[]
    #         table[current_date.date()]=[]
    #         #add all time data to table
    #         #iterate through hours
    #         for set in tmp:
    #             tmp_dict={keys[0]:dt.datetime.fromisoformat(set[0]).time()}
    #             #iterate through tuple
    #             for field_id in range(len(set)-1):
    #                 if set[field_id+1]!=None:
    #                     tmp_dict[keys[field_id+1]]=set[field_id+1]
    #             #append dict to list            
    #             table[current_date.date()].append(tmp_dict)
        
    #     #next day
    #     current_date=current_date+delta
    
    #get all days at 1 pass
    SQL_querry=f'SELECT * FROM dane WHERE date(date) BETWEEN date("{str(date_from.date())}") AND date("{str(date_to.date())}");'# ORDER BY datetime(date) ASC;'

    exec=cur.execute(SQL_querry)

    all_data=exec.fetchall()
    print(f'Pobrano z bazy w {time_meassure.time()-start}')
    #all_data=[(datetime, power_mom ...),(datetime, power_mom ...)...]
    #close database connection
    con.close()
    #iterate throuh rows in database
    for data in all_data:
        #data=(datetime, power_mom ...) - look into keys.py
        date_time=dt.datetime.fromisoformat(data[0])
        date=date_time.date()
        time=date_time.time()
        if not date in table.keys():
            table[date]=[]
        tmp_dict={'time':time}
        for field_id in range(len(data)-1):
            if data[field_id+1]!=None:
                #there is data in this column in database
                tmp_dict[keys[field_id+1]]=data[field_id+1]
            else:
                #there is no data in this column in database
                tmp_dict[keys[field_id+1]]='---'
        table[date].append(tmp_dict)

    end=time_meassure.time()
    print(f'Gather took: {end-start}s')
    
    return table

def get_int(base, date_from_p=0,date_to_p=0,memory=False):
    #takes data from sqlite database
    #date_from, date_to - time interval, have to be datetime type
    #returns: {day1: [
    #           {time,power kW, summarized power consumption kWh, T1 power consumpion kWh, , T2 power consumpion kWh, , T3 power consumpion kWh},
    #           {...}
    #               ],
    #          day2: [{time,power kW, summarized power consumption kWh, T1 power consumpion kWh, , T2 power consumpion kWh, , T3 power consumpion kWh},{...}],
    #           .
    #           .
    #           .}
    # date_from=0 - data from the beggining
    # date_to=0 - data up to now
    #base - full base path
    start=time_meassure.time()
    #copy in case of changing
    date_from=date_from_p
    date_to=date_to_p
    if (date_from==0):
        date_from=dt.datetime(2022,10,1,0,0,0)
    if (date_to==0):
        date_to=dt.datetime.now()
    if date_from>date_to:
        tmp=date_to
        date_to=date_from
        date_from=tmp

    #delta=dt.timedelta(days=1)
    #current_date=date_from

    #table with data
    table={}

    #get data from db
    #con=sqlite3.connect('/home/krzysztof/Pomiary/baza_pomiarow.db')
    try:
        if memory:
            con_a=sqlite3.connect(base)
        else:
            con=sqlite3.connect(base)
    except:
        return table
    
    #copy database to the memory
    if memory:
        con=sqlite3.connect(':memory:')
        con_a.backup(con)
        con_a.close()
    
    cur=con.cursor()

    #datetime in base is in seconds hence the date_to must be the lase second in this day
    tim=dt.time(23,59,59)
    date_to=dt.datetime.combine(date_to.date(),tim)

    #remove time if it is
    tim=dt.time(0,0,0)
    date_from=dt.datetime.combine(date_from.date(),tim)
    #get all days at 1 pass
    SQL_querry=f'SELECT * FROM dane WHERE date BETWEEN {str(int(date_from.timestamp()))} AND {str(int(date_to.timestamp()))};'# ORDER BY date ASC;'

    exec=cur.execute(SQL_querry)

    all_data=exec.fetchall()
    print(f'Pobrano z bazy w {time_meassure.time()-start}')
    #all_data=[(datetime, power_mom ...),(datetime, power_mom ...)...]
    #close database connection
    con.close()
    #iterate throuh rows in database
    for data in all_data:
        #data=(datetime, power_mom ...) - look into keys.py
        date_time=dt.datetime.fromtimestamp(data[0])
        date=date_time.date()
        time=date_time.time()
        if not date in table.keys():
            table[date]=[]
        tmp_dict={'time':time}
        for field_id in range(len(data)-1):
            if data[field_id+1]!=None:
                #there is data in this column in database
                tmp_dict[keys[field_id+1]]=data[field_id+1]
            else:
                #there is no data in this column in database
                tmp_dict[keys[field_id+1]]='---'
        table[date].append(tmp_dict)

    end=time_meassure.time()
    print(f'Gather took: {end-start}s')
    
    return table