import pickle
import sys
import time

import zmq

import constPipe

me = str(sys.argv[1])
address1 = "tcp://" + constPipe.SRC2 + ":" + constPipe.PORT2  # 1st task src
address2 = "tcp://" + constPipe.SRC3 + ":" + constPipe.PORT3  # 2nd task src
address3 = "tcp://" + constPipe.SRC4 + ":" + constPipe.PORT4  # 2nd task src

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)  # create a pull socket

pull_socket.connect(address1)  # connect to task source 1
pull_socket.connect(address2)  # connect to task source 2
pull_socket.connect(address3)  # connect to task source 2

time.sleep(1) 

print("reducer {} started".format(me))

count_dict_total = {}

while True:
    work = pickle.loads(pull_socket.recv())  # receive work from a source
    dic = work[1]
    #print(dic)
    for word, count in dic.items():
        count_dict_total[word] = count_dict_total.get(word, 0) + count
    #print("{} received workload {} from {}".format(me, work[1], work[0]))
    print(count_dict_total)
