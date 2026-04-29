import constRPC
import threading
import time

from context import lab_channel


class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self


class Client(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.chan = lab_channel.Channel()
        self.client = self.chan.join('client')
        self.server = None
        self.ready = threading.Event()

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')
        self.ready.set()

    def stop(self):
        self.chan.leave('client')

    def do_something_else(self):
        print("main thread is doing something else")
        pass

    def append_async(self, data, db_list, callback):
        def run(data, db_list):
            ret = self.append(data, db_list)
            callback(ret)
        thread = threading.Thread(target=run, args=(data, db_list))
        thread.start()

    def receive_msg(self, data):
        if isinstance(data,  str):
            print(f"Received message from server: {data}")
        else:
            print("Result: {}".format(data.value))

    def append(self, data, db_list):
        assert isinstance(db_list, DBList)
        msglst = (constRPC.APPEND, data, db_list)  # message payload
        self.chan.send_to(self.server, msglst)  # send msg to server
        msgrcv = self.chan.receive_from(self.server)  # wait for response
        return(msgrcv[1])  # pass it to caller

class Server:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.server = self.chan.join('server')
        self.timeout = 3

    @staticmethod
    def append(data, db_list):
        assert isinstance(db_list, DBList)  # - Make sure we have a list
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)
        while True:
            msgreq = self.chan.receive_from_any(self.timeout)  # wait for any request
            if msgreq is not None:
                client = msgreq[0]  # see who is the caller
                msgrpc = msgreq[1]  # fetch call & parameters
                if constRPC.APPEND == msgrpc[0]:  # check what is being requested
                    #TODO funktioniert nicht so gut
                    #self.chan.send_to({client}, f"request received")  # return response
                    result = self.append(msgrpc[1], msgrpc[2])  # do local call
                    time.sleep(10)
                    self.chan.send_to({client}, result)  # return response
                else:
                    pass  # unsupported request, simply ignore
