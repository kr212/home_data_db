import datetime
import crc
import serial
import struct
#import byte_to_float


class MeterInvalidFunctionCodeException(Exception):
    """Exception raised in case of wrong register name"""
    pass

class MeterWrongRegisterAddressException(Exception):
    """Exception raised in case of wrong register name"""
    pass

class MeterWrongDataLengthException(Exception):
    """Exception raised in case of wrong register name"""
    pass

class MeterComunicationException(Exception):
    """Exception raised in case of wrong register name"""
    pass

class MeterCRCException(Exception):
    """Exception raised in case of wrong CRC of received message"""
    pass


class Meter():
    registers={
        'Serial number':{'fc_read':0x03,'reg_h':0x00,'reg_l':0x00,'length':4,'type':'int','unit':''},
        'Meter ID':{'fc_read':0x03,'reg_h':0x00,'reg_l':0x02,'length':2,'type':'int','unit':'','fc_write':0x06},
        'Baud Rate':{'fc_read':0x03,'reg_h':0x00,'reg_l':0x03,'length':2,'type':'int','unit':'bps','fc_write':0x06},
        'Software Version':{'fc_read':0x03,'reg_h':0x00,'reg_l':0x04,'length':4,'type':'float','unit':''},
        'Hardware Version':{'fc_read':0x03,'reg_h':0x00,'reg_l':0x06,'length':4,'type':'float','unit':''},
        'CT Rate':{'fc_read':0x03,'reg_h':0x00,'reg_l':0x08,'length':2,'type':'int','unit':''},
        'S0 output rate':{'fc_read':0x03,'reg_h':0x00,'reg_l':0x09,'length':4,'type':'float','unit':'imp/kWh'},
        'Combined Code':{'reg_l':0x0B,'reg_h':0x00,'length':2,'type':'int','fc_read':0x03,'unit':'','fc_write':0x06},
        #'HOLIDAY-WEEKEND T':{'reg_l':0x0C,'reg_h':0x00,'length':2,'type':'int','fc_read':0x03,'unit':''},
        'Cycle time':{'reg_l':0x0D,'reg_h':0x00,'length':2,'type':'int','fc_read':0x03,'unit':'s','fc_write':0x06},
        'L1 Voltage':{'reg_l':0x0E,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'V'},
        'L2 Voltage':{'reg_l':0x10,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'V'},
        'L3 Voltage':{'reg_l':0x12,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'V'},
        'Grid frequency':{'reg_l':0x14,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'Hz'},
        'L1 Current':{'reg_l':0x16,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'A'},
        'L2 Current':{'reg_l':0x18,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'A'},
        'L3 Current':{'reg_l':0x1A,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'A'},
        'Total Active Power':{'reg_l':0x1C,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kW'},
        'L1 Active Power':{'reg_l':0x1E,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kW'},
        'L2 Active Power':{'reg_l':0x20,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kW'},
        'L3 Active Power':{'reg_l':0x22,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kW'},
        'Total Reactive Power':{'reg_l':0x24,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kVar'},
        'L1 Reactive Power':{'reg_l':0x26,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kVar'},
        'L2 Reactive Power':{'reg_l':0x28,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kVar'},
        'L3 Reactive Power':{'reg_l':0x2A,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kVar'},
        'Total Apparent Power':{'reg_l':0x2C,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kVA'},
        'L1 Apparent Power':{'reg_l':0x2E,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kVA'},
        'L2 Apparent Power':{'reg_l':0x30,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kVA'},
        'L3 Apparent Power':{'reg_l':0x32,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':'kVA'},
        'Total Power Factor':{'reg_l':0x34,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':''},
        'L1 Power Factor':{'reg_l':0x36,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':''},
        'L2 Power Factor':{'reg_l':0x38,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':''},
        'L3 Power Factor':{'reg_l':0x3A,'reg_h':0x00,'length':4,'type':'float','fc_read':0x03,'unit':''},
        'Total Active Energy':{'reg_l':0x00,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'L1 Total Active Energy':{'reg_l':0x02,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'L2 Total Active Energy':{'reg_l':0x04,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'L3 Total Active Energy':{'reg_l':0x06,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'Forward Active Energy':{'reg_l':0x08,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'L1 Forward Active Energy':{'reg_l':0x0A,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'L2 Forward Active Energy':{'reg_l':0x0C,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'L3 Forward Active Energy':{'reg_l':0x0E,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'Reverse Active Energy':{'reg_l':0x10,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'L1 Reverse Active Energy':{'reg_l':0x12,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'L2 Reverse Active Energy':{'reg_l':0x14,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'L3 Reverse Active Energy':{'reg_l':0x16,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'Total Reactive Energy':{'reg_l':0x18,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'L1 Reactive Energy':{'reg_l':0x1A,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'L2 Reactive Energy':{'reg_l':0x1C,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'L3 Reactive Energy':{'reg_l':0x1E,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'Forward Reactive Energy':{'reg_l':0x20,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'L1 Forward Reactive Energy':{'reg_l':0x22,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'L2 Forward Reactive Energy':{'reg_l':0x24,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'L3 Forward Reactive Energy':{'reg_l':0x26,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'Reverse Reactive Energy':{'reg_l':0x28,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'L1 Reverse Reactive Energy':{'reg_l':0x2A,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'L2 Reverse Reactive Energy':{'reg_l':0x2C,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'L3 Reverse Reactive Energy':{'reg_l':0x2E,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T1 Total Active Energy':{'reg_l':0x30,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T1 Forward Active Energy':{'reg_l':0x32,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T1 Reverse Active Energy':{'reg_l':0x34,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T1 Total Reactive Energy':{'reg_l':0x36,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T1 Forward Reactive Energy':{'reg_l':0x38,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T1 Reverse Reactive Energy':{'reg_l':0x3A,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T2 Total Active Energy':{'reg_l':0x3C,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T2 Forward Active Energy':{'reg_l':0x3E,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T2 Reverse Active Energy':{'reg_l':0x40,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T2 Total Reactive Energy':{'reg_l':0x42,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T2 Forward Reactive Energy':{'reg_l':0x44,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T2 Reverse Reactive Energy':{'reg_l':0x46,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T3 Total Active Energy':{'reg_l':0x48,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T3 Forward Active Energy':{'reg_l':0x4A,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T3 Reverse Active Energy':{'reg_l':0x4C,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T3 Total Reactive Energy':{'reg_l':0x4E,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T3 Forward Reactive Energy':{'reg_l':0x50,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T3 Reverse Reactive Energy':{'reg_l':0x52,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T4 Total Active Energy':{'reg_l':0x54,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T4 Forward Active Energy':{'reg_l':0x56,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T4 Reverse Active Energy':{'reg_l':0x58,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kWh'},
        'T4 Total Reactive Energy':{'reg_l':0x5A,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T4 Forward Reactive Energy':{'reg_l':0x5C,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'T4 Reverse Reactive Energy':{'reg_l':0x5E,'reg_h':0x01,'length':4,'type':'float','fc_read':0x03,'unit':'kVarh'},
        'Time':{'reg_l':0x3C,'reg_h':0x00,'length':8,'fc_read':0x03,'fc_write':0x10,'type':'data','unit':''},
        'Time Interval 1':{'reg_l':0x00,'reg_h':0x03,'length':24,'fc_read':0x03,'fc_write':0x10,'type':'data','unit':''},
        'Time Interval 2':{'reg_l':0x0C,'reg_h':0x03,'length':24,'fc_read':0x03,'fc_write':0x10,'type':'data','unit':''},
        'Time Interval 3':{'reg_l':0x18,'reg_h':0x03,'length':24,'fc_read':0x03,'fc_write':0x10,'type':'data','unit':''},
        'Time Interval 4':{'reg_l':0x24,'reg_h':0x03,'length':24,'fc_read':0x03,'fc_write':0x10,'type':'data','unit':''},
        'Time Interval 5':{'reg_l':0x30,'reg_h':0x03,'length':24,'fc_read':0x03,'fc_write':0x10,'type':'data','unit':''},
        'Time Interval 6':{'reg_l':0x3C,'reg_h':0x03,'length':24,'fc_read':0x03,'fc_write':0x10,'type':'data','unit':''},
        'Time Interval 7':{'reg_l':0x48,'reg_h':0x03,'length':24,'fc_read':0x03,'fc_write':0x10,'type':'data','unit':''},
        'Time Interval 8':{'reg_l':0x54,'reg_h':0x03,'length':24,'fc_read':0x03,'fc_write':0x10,'type':'data','unit':''},
        'Time Zone':{'reg_l':0x60,'reg_h':0x03,'length':24,'fc_read':0x03,'fc_write':0x10,'type':'data','unit':''},
        'Holiday Weekend T':{'reg_l':0x0C,'reg_h':0x00,'length':2,'fc_read':0x03,'fc_write':0x06,'type':'data','unit':''}

    }
    
    def __init__(self,port,id,return_unit=False):
        self.port=port
        self.id=id
        self.return_unit=return_unit

    def _message(self,data,rw='r',payload=[]):
        """prepare data to send to Meter, only for read action!!!
        accepts a dictionary, for example: {'fc_read':0x03,'reg_h':0x00,'reg_l':0x00,'length':4,'type':'int','unit':''}"""
        #packet frame starts with meter id
        send=[self.id]
        #then function code
        if rw=='w':
            send.append(data['fc_write'])
        else:
            send.append(data['fc_read'])

        #register address
        send.append(data['reg_h'])
        send.append(data['reg_l'])
        #only in write mode and if length>2 we skip this
        if not (rw=='w' and data['length']==2):
            #always 0?
            send.append(0x00)
            #data length in words
            send.append(int(data['length']/2))
        for pp in payload:
            send.append(pp)
        #calculate crc
        crc_c=crc.crc(send)
        #add ccr at the end of frame
        send.append(crc_c[0])
        send.append(crc_c[1])
        print('To send:')
        print(send)
        return serial.to_bytes(send)

    def _check_error(self,bytes,proper_answer):
        """checks if there was an error in received data
        meter should send in 2nd byte the function code that was used, if it is not that number there was an error, its number is in 3rd byte"""
        if bytes[1]!=proper_answer:
            #read error information
            match bytes[2]:
                case 0x01: raise MeterInvalidFunctionCodeException
                case 0x02: raise MeterWrongRegisterAddressException
                case 0x03: raise MeterWrongDataLengthException
                case _: raise MeterComunicationException
    
    def _CRC_check(self,data):
        if crc.crc(data[:-2])!=(data[-2],data[-1]):
            raise MeterCRCException

    def _send_receive_read(self, register):
        """perform send and receive actions including errors check, for read action only
        returns payload: packet except first 3 and last 4 bytes
        input: register for example:{'fc_read':0x03,'reg_h':0x00,'reg_l':0x00,'length':4,'type':'int','unit':''}"""
        
        message_tmp=self._message(register)

        self.port.write(self._message(register))
        #read first 3 bytes in case of error (won't be more in that case)
        read=self.port.read(3)
        
        self._check_error(read,register['fc_read'])
        
        packet_length=read[2]
        read2=self.port.read(packet_length+2) #length of packet is stored in 3rd byte, +2 because there are 2 bytes od CRC
        payload=read2[:-2]
    
        #add crc check of received data!!!!!!!!!!!!!!!!!!!! read+read2=full packet
        self._CRC_check(read+read2)
        #check if there is enough data
        if len(payload)!=packet_length:
            raise MeterWrongDataLengthException
        
        return payload
    
    def _send_receive_write(self, register,payload_d):
        """perform send and receive actions including errors check, for write action only
        returns true or false
        input: register for example:{'fc_read':0x03,'reg_h':0x00,'reg_l':0x00,'length':4,'type':'int','unit':''}"""
        
        self.port.write(self._message(register,'w',payload_d))
        #read first 3 bytes in case of error (won't be more in that case)
        read=self.port.read(3)
        
        self._check_error(read,register['fc_write'])
        
        packet_length=5  #always the same length?
        read2=self.port.read(packet_length) 
        read=read+read2

        print('Received:')
        print(read)
    
        #add crc check of received data!!!!!!!!!!!!!!!!!!!! read+read2=full packet
        self._CRC_check(read)
        #check if there is enough data
        if read[2]==register['reg_h'] and read[3]==register['reg_l'] and read[5]==int(register['length']/2):
            return True
        else:
            return False

    def _int_to_BCD(self,number):
        tmp1=number % 10
        tmp2=int(number / 10)

        return (tmp2<<4 | tmp1)
    
    def _BCD_to_int(self,BCD):
        tmp1=BCD & 0b1111
        tmp2=(BCD >> 4) & 0b1111

        return (tmp1+tmp2*10)

    
    def read(self,register_name):
        """Read value from meter register and return it (only values from 'registers')"""

        #check if the register/value name is correct
        if register_name not in Meter.registers.keys():
            return None
        
        data=self._send_receive_read(Meter.registers[register_name])

        if Meter.registers[register_name]['type']=='float':
            (value,)=struct.unpack('>f',data)
        elif Meter.registers[register_name]['type']=='int':
            value=int.from_bytes(data,'big')
        elif Meter.registers[register_name]['type']=='data':
            value=[]
            for kk in data:
                value.append(self._BCD_to_int(kk))
        
        if self.return_unit:
            return (value,Meter.registers[register_name]['unit'])
        else:
            return value

    def get_time(self):
        """reads time and data froom meter
        answer from meter: address, fc_read, length, s, m, h, week_day, day, month, year, ?? , CRC,CRC"""
        
        
        data=self._send_receive_read(Meter.registers['Time'])
        
        return datetime.datetime(self._BCD_to_int(data[6]),self._BCD_to_int(data[5]),self._BCD_to_int(data[4]),self._BCD_to_int(data[2]),self._BCD_to_int(data[1]),self._BCD_to_int(data[0]))

    def set_time(self,date_time='now'):
        """sets date and time in the Meter
        packet: id, fc_write, addr_h, addr_l, 0x00, length/2, 0x08?, s, m, h, week_day 1-7, day, month, year, 0x00,CRC,CRC"""
        #check the date
        if date_time=='now':
            set=datetime.datetime.now()
        else:
            set=date_time
        #raw payload, not in BCD format
        payload_send=[0x08,set.second,set.minute,set.hour,set.isoweekday(),set.day, set.month, set.year % 100, 0x00 ]
        
        #convert values to BCD (0x08 and 0x00 won't be changed)
        for pp in range(len(payload_send)):
            payload_send[pp]=self._int_to_BCD(payload_send[pp])

        return self._send_receive_write(Meter.registers['Time'],payload_send)

    def get_interval(self,number):
        """reads the 'number' interval from Meter
        it conains the time when tariff starts
        answer should be: address, fc_read, length, (hh ,mm, tariff )x8, crc,crc
        return list with 8 tuples (time,tariff)"""
        if (number <1) or (number>8):
            return None
        
        data=self._send_receive_read(Meter.registers[f'Time Interval {number}'])

        intervals=[]
        for i in range(8):
            #calculate index for hours and change them to ints
            hours=self._BCD_to_int( data[i*3] )
            minutes=self._BCD_to_int( data[(i*3)+1] )
            tarrif=data[(i*3)+2] 
            intervals.append( (datetime.time(hours,minutes),tarrif))
        return intervals

    def set_interval(self,number,h1_list,m1=0x00,t1=0x00,h2=0x00,m2=0x00,t2=0x00,h3=0x00,m3=0x00,t3=0x00,h4=0x00,m4=0x00,t4=0x00,h5=0x00,m5=0x00,t5=0x00,h6=0x00,m6=0x00,t6=0x00,h7=0x00,m7=0x00,t7=0x00,h8=0x00,m8=0x00,t8=0x00):
        """sets requested interval with data
        accepts list of tariffs (like from get_interval, don't have to have 8 elements, can be less) or separate values of hours, minutes and tariffs
        packet:id, fc_write, addr_h,addr_l,0x00, length/2,0x18?,(hh ,mm, tariff )x8, crc,crc"""

        if (number <1) or (number>8):
            return False

        if type(h1_list)==list:
            #got list
            payload_send=[]
            for k in range(24):
                payload_send.append(0x00)
            for set in range(len(h1_list)):
                payload_send[set*3]=self._int_to_BCD(h1_list[set][0].hour)
                payload_send[set*3+1]=self._int_to_BCD(h1_list[set][0].minute)
                payload_send[set*3+2]=h1_list[set][1]
        else:
            #got integers
            payload_send=[h1_list,m1,t1,h2,m2,t2,h3,m3,t3,h4,m4,t4,h5,m5,t5,h6,m6,t6,h7,m7,t7,h8,m8,t8]
            #convert values to BCD 
            for pp in range(len(payload_send)):
                payload_send[pp]=self._int_to_BCD(payload_send[pp])
        
        #add0x18 at the begining
        payload_send=[0x18]+payload_send

        return self._send_receive_write(Meter.registers[f'Time Interval {number}'],payload_send)
            

    def get_zone(self):
        """reads the zone from Meter
        it conains the date when interval starts
        answer should be: address, fc_read, length, (mm ,dd, interval )x8, crc,crc
        return list with 8 tuples (date,interval)"""
        
        data=self._send_receive_read(Meter.registers['Time Zone'])

        zone=[]
        for i in range(8):
            #calculate index for months and change them to ints
            months=self._BCD_to_int( data[i*3] )
            days=self._BCD_to_int( data[(i*3)+1] )
            interval=data[(i*3)+2] 
            if (months==0) or (days==0):
                #no more data
                break
            zone.append( (datetime.date(year=2000,month=months,day=days),interval))
        return zone

    def set_zone(self,m1_list,d1=0x00,i1=0x00,m2=0x00,d2=0x00,i2=0x00,m3=0x00,d3=0x00,i3=0x00,m4=0x00,d4=0x00,i4=0x00,m5=0x00,d5=0x00,i5=0x00,m6=0x00,d6=0x00,i6=0x00,m7=0x00,d7=0x00,i7=0x00,m8=0x00,d8=0x00,i8=0x00):
        """sets zone with data
        accepts list of intervals (like from get_zone, don't have to have 8 elements, can be less) or separate values of months, days and intervals
        packet:id, fc_write, addr_h,addr_l,0x00, length/2, 0x18?, (hh ,mm, tariff )x8, crc,crc"""

        
        if type(m1_list)==list:
            #got list
            payload_send=[]
            for k in range(24):
                payload_send.append(0x00)
            for set in range(len(m1_list)):
                payload_send[set*3]=self._int_to_BCD(m1_list[set][0].month)
                payload_send[set*3+1]=self._int_to_BCD(m1_list[set][0].day)
                payload_send[set*3+2]=m1_list[set][1]
        else:
            #got integers
            payload_send=[m1_list,d1,i1,m2,d2,i2,m3,d3,i3,m4,d4,i4,m5,d5,i5,m6,d6,i6,m7,d7,i7,m8,d8,i8]
            #convert values to BCD 
            for pp in range(len(payload_send)):
                payload_send[pp]=self._int_to_BCD(payload_send[pp])
        
        #add0x18 at the begining
        payload_send=[0x18]+payload_send

        return self._send_receive_write(Meter.registers['Time Zone'],payload_send)

    def get_week_hol(self):
        """reads the holiday and weekend intervals from Meter
        it conains the date when interval starts
        answer should be: address, fc_read, length, holiday, weekend, crc,crc
        return tuple with 2 values of intervals, for weekend and for holidays"""
        
        data=self._send_receive_read(Meter.registers['Holiday Weekend T'])

        return (data[0],data[1])

    def set_week_hol(self,weekend=0x01,holiday=0x00):
        """sets intervals for weekend and holidays
        accepts two values 0 to 8
        packet:id, fc_write, addr_h,addr_l,0x00, weekend, holiday, crc,crc"""

        if (weekend>=0) and (weekend<=8) and (holiday>=0) and (holiday<=8):
            payload_send=[weekend,holiday]
        else:
            return False

        return self._send_receive_write(Meter.registers['Holiday Weekend T'],payload_send)
    
    def set_ID(self,ID):
        """sets the modbus ID of Meter"""
        if (ID<1) or (ID>247):
            return False
        
        res= self._send_receive_write(Meter.registers['Meter ID'],[0x00,ID])

        #change ID in object in case of proper change
        if res:
            self.id=ID
        
        return res
    
    def set_baud(self,baud=9600):
        """sets the modbus baudrate of Meter"""
        rates=[1200,2400,4800,9600]
        if baud not in rates:
            return False
        high_b=(baud>>8) & 0b11111111
        low_b=baud & 0b11111111

        return self._send_receive_write(Meter.registers['Baud Rate'],[high_b,low_b])
    
    def set_code(self,code=1):
        """sets the combined code of Meter
        1: Total=forward
        5: Total=forward + reverse
        9: total=forward - reverse"""
        codes=[1,5,9]
        if code not in codes:
            return False
        

        return self._send_receive_write(Meter.registers['Combined Code'],[0x00,code])
    
    def set_cycle_time(self,time=5):
        """sets cycle time of Meter, how long the value is being displayed on LCD, 1s - 30s"""

        if (time<1) or (time>30):
            return False
        
        return self._send_receive_write(Meter.registers['Cycle time'],[0x00,time])
