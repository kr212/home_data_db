import threading
import logging


import meter
import storage
import buffer

logging.basicConfig(level=logging.INFO)

orwe517=meter.Meter()
store=storage.Storage()
buf_orwe517_storage=buffer.Buffer()
buf_control=buffer.Buffer()


orwe517_thr=threading.Thread(target=orwe517.run,args=(buf_orwe517_storage,buf_control))
store_thr=threading.Thread(target=store.run,args=(buf_orwe517_storage,buf_control))

orwe517_thr.start()
store_thr.start()

inp=input('>>')
buf_control.put([inp])

orwe517_thr.join()
store_thr.join()




