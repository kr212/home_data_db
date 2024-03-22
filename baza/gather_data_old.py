import os
import glob
import datetime as dt

holidays_const=[dt.datetime(2000,1,1),dt.datetime(2000,1,6),dt.datetime(2000,5,1),dt.datetime(2000,5,3),dt.datetime(2000,8,15),dt.datetime(2000,11,1),dt.datetime(2000,11,11),dt.datetime(2000,12,25),dt.datetime(2000,12,26)]
holidays_easter=[dt.datetime(2023,4,10),dt.datetime(2024,4,1),dt.datetime(2025,4,21)]
holidays_bc=[dt.datetime(2023,6,8),dt.datetime(2024,5,30),dt.datetime(2025,6,19)]

keys=["power","sum","T1","T2","T3","temp_water","temp_outside","pressure"]

def gather(dir,file, date_from=0,date_to=0):
    #takes data from files "pomiar_yyyy.mm"
    #date_from, date_to - time interval, have to be datetime type
    #returns: {"day1": [power kW, summarized power consumption kWh, T1 power consumpion kWh, , T2 power consumpion kWh, , T3 power consumpion kWh],
    #          "day2": [power kW, summarized power consumption kWh, T1 power consumpion kWh, , T2 power consumpion kWh, , T3 power consumpion kWh],
    #           .
    #           .
    #           .}
    # date_from=0 - data from the beggining
    # date_to=0 - data up to now
    # files for example: '/home/krzysztof/Pomiary/pomiar_'+'yyyy.mm'

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
    find_str=str(date_from.year)+'.'+str(date_from.month)

    for i in range(len(found_files)):
        if found_files[i].find(find_str)!=-1:
            list_start=i
            break
    
    #ending of file list
    list_end=len(found_files) 

    #remove the ending of the list from valid end date
    find_str=str(date_to.year)+'.'+str(date_to.month)
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
            table[date].append({'time':time,'power':float(data_spl[1]),'sum':float(data_spl[2]),'T1':float(data_spl[3]),'T2':float(data_spl[4]),'T3':float(data_spl[5])})
        
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
    
    return table


def is_holiday(day):
#check if date is a holiday
    for d in holidays_const:
        if (d.month==day.month) and (d.day==day.day):
            return True
    if (day in holidays_bc) or (day in holidays_easter):
        return True
    return False


