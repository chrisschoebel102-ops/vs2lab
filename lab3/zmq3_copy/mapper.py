import pickle
import sys
import time
import re

import zmq

import constPipe

me = str(sys.argv[1])
address1 = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT1  # 1st task src

match me:
    case "1":
        src = constPipe.SRC2
        prt = constPipe.PORT2
    case "2":
        src = constPipe.SRC3
        prt = constPipe.PORT3
    case "3":
        src = constPipe.SRC4
        prt = constPipe.PORT4
    case _:
        pass

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)  # create a pull socket
push_socket = context.socket(zmq.PUSH)  # create a push socket

address = "tcp://" + src + ":" + prt  # how and where to connect
push_socket.bind(address)  # bind socket to address
pull_socket.connect(address1)  # connect to task source 1

time.sleep(1) 

print("mapper {} started".format(me))

while True:
    work = pickle.loads(pull_socket.recv())  # receive work from a source
    print("{} received workload {} from {}".format(me, work[1], work[0]))
    count_dict = {} # initialize / reset count dict
    line = work[1] # get the actual line
    line = line.replace("\n", "")
    line = line.strip()


    pattern = r"\w"
    re.sub(pattern, r"", line)
    words = line.split(" ")
    for w in words:
        if w not in count_dict:
            count_dict[w] = 1
        else:
            count_dict[w] += 1

    workload = count_dict  # compute workload
    push_socket.send(pickle.dumps((me, workload)))
