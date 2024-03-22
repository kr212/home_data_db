class AHT20:
    def __init__(self,obiekt):
        #jako argument trzeba podać obiekt stworzony z EasyMCP2221
        #przykład
        #dev=EasyMCP2221.Device()
        #bmp=dev.I2C_Slave(0x38)
        #bmp podaje się jako obiekt

        self.t_adjustment=2.0
        self.aht=obiekt

        #read status word - check calibration
        self.aht.write(0x71)

        self.data=self.aht.read(1)

        if not (self.data[0] &  0b00001000):
            #no calibration, must do
            self.aht.write(bytes([0xbe,0x08,0x00]))
        
    
    def read(self):
        #funkcja zwraca wartosc temperatury i wilgotności
        #temperatura:xx.xx, wilg xx.x %
        #send trigger for measurement
        self.aht.write(bytes([0xac,0x33,0x00]))
        
        #wait for busy set to 0
        self.busy=True
        while self.busy:
            self.aht.write(0x71)
            self.data=self.aht.read(1)
            if not (self.data[0] & 0b10000000):
                self.busy=False
        
        self.data=self.aht.read(6)

        self.humidity=float((self.data[1]<<12) | (self.data[2]<<4) | (self.data[3]>>4))/pow(2,20)*100
        self.temp=float(((self.data[3] & 0b00001111)<<16) | (self.data[4]<<8) | (self.data[5]))/pow(2,20)*200-50

        return (round(self.temp,1)+self.t_adjustment),round(self.humidity,1)
