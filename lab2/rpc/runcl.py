import rpc
import logging
import time

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.start()
cl.ready.wait()

base_list = rpc.DBList({'foo'})
cl.append_async('bar', base_list, cl.receive_msg)
for i in range(15):
    cl.do_something_else()
    time.sleep(1)
cl.stop()    

