class BMP280:
    def __init__(self,obiekt):
        #jako argument trzeba podać obiekt stworzony z EasyMCP2221
        #przykład
        #dev=EasyMCP2221.Device()
        #bmp=dev.I2C_Slave(0x76)
        #bmp podaje się jako obiekt
        #self.t_adjustment=0.8
        self.t_adjustment=0.0
        
        self.bmp=obiekt

        #odczytanie parametrów korygujących wartości temperatury i cisnienia
        self.data=self.bmp.read_register(0x88,26)

        self.dig_T1=int.from_bytes(self.data[0:2],byteorder='little',signed=False)
        self.dig_T2=int.from_bytes(self.data[2:4],byteorder='little',signed=True)
        self.dig_T3=int.from_bytes(self.data[4:6],byteorder='little',signed=True)
        self.dig_P1=int.from_bytes(self.data[6:8],byteorder='little',signed=False)
        self.dig_P2=int.from_bytes(self.data[8:10],byteorder='little',signed=True)
        self.dig_P3=int.from_bytes(self.data[10:12],byteorder='little',signed=True)
        self.dig_P4=int.from_bytes(self.data[12:14],byteorder='little',signed=True)
        self.dig_P5=int.from_bytes(self.data[14:16],byteorder='little',signed=True)
        self.dig_P6=int.from_bytes(self.data[16:18],byteorder='little',signed=True)
        self.dig_P7=int.from_bytes(self.data[18:20],byteorder='little',signed=True)
        self.dig_P8=int.from_bytes(self.data[20:22],byteorder='little',signed=True)
        self.dig_P9=int.from_bytes(self.data[22:24],byteorder='little',signed=True)

        

        #ustwienie oversampling pressure=1, temp=1
        self.bmp.write_register(0xF4,0b10110100)
        #self.bmp.write_register(0xF5,0b00000000)
    
    def read(self):
        #funkcja zwraca wartosc temperatury i cisnienia
        #temperatura:xx.xx, cisn xxxxx.x
        #ustwienie oversampling temp=001, pressure=001, start pomiaru - tryb forced
        self.bmp.write_register(0xF4,0b00100110)
        
        #czekaj na odczyt temperatury
        while (self.bmp.read_register(0xF3,1)[0] & 0b00001000):
            pass

        #odczyt wszystkich rejestrów temperatury i ciśnienia
        self.data=self.bmp.read_register(0xF7,6)
        
        #int temperatury z rejestrów
        self.temp_int=(self.data[3] << 12) | (self.data[4] << 4) | (self.data[5] >> 4)
        
        #przekształcenie temperatury
        #zgodnie z dokumentacja
        self.var1=((self.temp_int >> 3) - (self.dig_T1 << 1)) * (self.dig_T2 >>  11)
        self.var2=(((((self.temp_int>>4) - self.dig_T1) * ((self.temp_int>>4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = self.var1 + self.var2
        self.T = (self.t_fine * 5 + 128) >> 8
        
        #int cisnienia z rejestrów
        self.pres_int=(self.data[0] << 12) | (self.data[1] << 4) | (self.data[2] >> 4)
        
        #przekształcenie cisnienia
        #zgodnie z dokumentacja
        self.var1 = (self.t_fine) - 128000
        self.var2 = self.var1 * self.var1 * self.dig_P6
        self.var2 = self.var2 + ((self.var1*self.dig_P5)<<17)
        self.var2 = self.var2 + (self.dig_P4<<35)
        self.var1 = ((self.var1 * self.var1 * self.dig_P3)>>8) + ((self.var1 * self.dig_P2)<<12)
        self.var1 = ((1<<47)+self.var1)*(self.dig_P1)>>33
        if (self.var1 == 0):
            return self.T, 0

        self.p = 1048576-self.pres_int
        self.p = int((((self.p<<31)-self.var2)*3125)/self.var1)
        self.var1 = ((self.dig_P9) * (self.p>>13) * (self.p>>13)) >> 25
        self.var2 = ((self.dig_P8) * self.p) >> 19
        self.p = ((self.p + self.var1 + self.var2) >> 8) + ((self.dig_P7)<<4)

        return round(self.T/100.0+self.t_adjustment,1), round(self.p/256,1)