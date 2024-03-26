import datetime

holidays_const=[datetime.datetime(2000,1,1),datetime.datetime(2000,1,6),datetime.datetime(2000,5,1),datetime.datetime(2000,5,3),datetime.datetime(2000,8,15),datetime.datetime(2000,11,1),datetime.datetime(2000,11,11),datetime.datetime(2000,12,25),datetime.datetime(2000,12,26)]


def now():
    #return string with current date and time, without .xxxxxx seconds
    return str(datetime.datetime.now()).split('.')[0]

def str_to_date(date_str):
    #returns datetime object from string
    return datetime.datetime.fromisoformat(date_str)
  
def press_sea_level(pressure,temp,height):
    #calculates the pressure at sea level
    #stopień baryczny
    h=8000*(1+0.004*temp)/pressure
    
    #ciśnienie na poziomie morza
    P=pressure+(height/h)
    
    #średnie ciśnienie
    Psr=(pressure+P)/2
    
    #średnia temperatura
    tpm=temp+(0.6*height)/100
    
    tsr=(temp+tpm)/2
    
    h=8000*(1+0.004*tsr)/Psr
    
    Pn=pressure+(height/h)
    
    return Pn

def color(fg=None,bg=None):
    if (fg==None) and (bg==None):
        return '\33[0m'

    fg_col={'black':30,'red':31,'green':32,'yellow':33,'blue':94,'magenta':35,'cyan':36,'white':37}
    #bg_col={'black':40,'red':41,'green':42,'yellow':43,'blue':44,'magenta':45,'cyan':46,'white':47}
    command='\33['
    end='m'

    if fg!=None:
        command+=f'{str(fg_col[fg])}'
        if bg!=None:
            command+=f';{str(fg_col[bg]+10)}'
    else:
        command+=f'{str(fg_col[bg]+10)}'
    return command+end

def _count_easter(year):
    """counts date of easter in year and returns the next day (Easter is always in Sunday, which is properly interpreted by Orno meter)
    Meeus/Jones/Butcher method"""

    a = year%19
    b = int(year/100)
    c = year%100
    d = int(b/4)
    e = b%4
    f = int((b+8)/25)
    g = int((b-f+1)/3)
    h = (19*a+b-d-g+15)%30
    i = int(c/4)
    k = c%4
    l = (32+2*e+2*i-h-k)%7
    m = int((a+11*h+22*l)/451)
    p = (h+l-7*m+114)%31
    day = p+1
    month = int((h+l-7*m+114)/31)
    
    delta=datetime.timedelta(days=1)
    #a im interested in the next day after easter
    return datetime.date(year,month,day)+delta

def _count_bc(year):
    """counts date of "Boże ciało" in year, 60 days after Easter (59 after the next day after easter)"""
    return _count_easter(year) + datetime.timedelta(days=59)

def is_holiday(day):
#check if date is a holiday in Poland
    for d in holidays_const:
        if (d.month==day.month) and (d.day==day.day):
            return True
    day_c=day
    if type(day_c)==datetime.datetime:
        day_c=day.date()
    if (day_c==_count_easter(day_c.year)) or (day_c == _count_bc(day_c.year)):
        return True
    return False