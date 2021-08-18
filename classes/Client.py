import numpy as np
import copy
import sys
import random

from classes.Packet import Packet
from classes.MarkovChain import *
from classes.Message import Message
from classes.Node import Node
from classes.Utilities import StructuredMessage, setup_logger, random_string
import experiments.Settings

class Client(Node):
    def __init__(self, env, conf, net, loggers=None, label=0, id=None, p2p=False):
        self.conf = conf

        if conf["message"]["msg_type"] == "IM":
            self.mc = MarkovChain(TELEGRAM_TRANSITION_PROBABILITIES)
        elif conf["message"]["msg_type"] == "Mail":
            self.mc = MarkovChain(MAIL_TRANSITION_PROBABILITIES)

        super().__init__(env=env, conf=conf, net=net, loggers=loggers, id=id)


    def schedule_retransmits(self):
        pass

    def schedule_message(self, message):
        #  This function is used in the transcript mode
        ''' schedule_message adds given message into the outgoing client's buffer. Before adding the message
            to the buffer the function records the time at which the message was queued.'''

        print("> Scheduled message")
        current_time = self.env.now
        message.time_queued = current_time
        for pkt in message.pkts:
            pkt.time_queued = current_time
        self.add_to_buffer(message.pkts)


    def print_msgs(self):
        ''' Method prints all the messages gathered in the buffer of incoming messages.'''
        for msg in self.msg_buffer_in:
            msg.output()

    def get_msg_size(self):
        if self.conf["message"]["msg_type"] == "IM":
            state = self.mc.sample()
            size = TELEGRAM_AVG_SIZES_BYTES[state]
        elif self.conf["message"]["msg_type"] == "Mail":
            state = self.mc.sample()
            size = MAIL_AVG_SIZES_BYTES[state]
        else:
            size = random.randint(self.conf["message"]["min_msg_size"], self.conf["message"]["max_msg_size"])

        return size
