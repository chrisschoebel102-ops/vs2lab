"""
Client and server using classes
"""

import logging
import socket

import const_cs
from context import lab_logging
import json

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

# pylint: disable=logging-not-lazy, line-too-long

class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True
    _telefon_db = {f"Nutzer{i}": i for i in range(500)}

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))

    def serve(self):
        """ Serve echo """
        self.sock.listen(1)
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                while True:  # forever
                    data = connection.recv(1024).decode("ascii")  # receive data from client
                    if not data:
                        break  # stop if client stopped
                    #-----------#
                    if "GETALL" in data:
                        value = json.dumps(self._telefon_db)
                        connection.send(value.encode('ascii'))
                        connection.send()
                    elif "GET" in data:
                        split = data.split(" ")
                        name = split[1]
                        value = self._telefon_db[name]
                        connection.send(str(value).encode('ascii'))
                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts
        self.sock.close()
        self._logger.info("Server down.")

    def get(self, name=""):
        pass

    def getall(self):
        pass


class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    def call(self, msg_in="Hello, world"):
        """ Call server """
        self.sock.send(msg_in.encode('ascii'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('ascii')
        print(msg_out)  # print the result
        self.sock.close()  # close the connection
        self.logger.info("Client down.")
        return msg_out

    def get(self, name=""):
        msg = f"GET {name}"
        self.sock.send(msg.encode('ascii'))

        data = self.sock.recv(1024)
        ans = data.decode("ascii")
        self.logger.info(f"Client received answer: {ans}")
        return ans

    def getall(self):
        msg = f"GETALL"
        self.sock.send(msg.encode('ascii'))

        data = b""
        while True:
            d = self.sock.recv(1024)
            if not d:
                break
            data += d

        ans = data.decode("ascii")
        ans_dict = json.loads(ans)
        self.logger.info(f"Client received answer: {ans_dict}")
        return ans_dict

    def close(self):
        """ Close socket """
        self.sock.close()
