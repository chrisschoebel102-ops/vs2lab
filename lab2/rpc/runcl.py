import rpc
import logging

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.start()
cl.ready.wait()

base_list = rpc.DBList({'foo'})
cl.append_async('bar', base_list, cl.receive_msg)
cl.do_something_else()
cl.do_something_else()

