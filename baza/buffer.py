import threading

class Buffer:
    def __init__(self):
        self.data=[]
        self._lock=threading.Lock()

    def put(self,data):
        #store data in buffer
        with self._lock:
            self.data=[data]
        

    def get(self):
        #get data from buffer, do not erase it
        with self._lock:
            if len(self.data)>0:
                self.tmp=self.data[0]
            else:
                self.tmp=[]
        
        return self.tmp

    def clear(self):
        #clear the buffer
        with self._lock:
            self.data=[]
        

    def empty(self):
        #check if buffer is empty
        with self._lock:
            self.length=len(self.data)
        

        if self.length==0:
            return True
        
        return False
