import string
from os import urandom
import logging
import logging.handlers
from experiments.Settings import *
import json
import numpy
from string import ascii_letters
import random
import numpy as np

def random_string(size):
    return ''.join(random.choice(ascii_letters) for _ in range(size))

def get_exponential_delay(avg_delay, cache=[]):
    if cache == []:
        cache.extend(list(numpy.random.exponential(avg_delay, 10000)))

    return cache.pop()

def translation_dictionaries(clients):
    # get unique IDs and sort them alphabetically
    old_ids = sorted(list(set([client.id for client in clients])))
    # generate new ids
    new_ids = list(range(len(old_ids)))

    translation_dict = {old:new for (old, new) in zip(old_ids, new_ids)}
    inv_translation_dict = {v: k for k, v in translation_dict.items()}

    return translation_dict, inv_translation_dict

def get_recipients(clients, sender_id, topology, id_to_nr):
    # get the nr of the sender
    sender_nr = id_to_nr[sender_id]

    # get the nrs of the recipients
    recipient_nrs = np.nonzero(topology[sender_nr, :])[0]

    # get the recipients
    recipients = [rec for rec in clients if id_to_nr[rec.id] in recipient_nrs]

    return recipients

class StructuredMessage(object):
    def __init__(self, metadata):
        self.metadata = metadata

    def __str__(self):
        return ';'.join(str(x) for x in self.metadata)  # json.dumps(self.metadata)



def float_equlity(tested, correct=1.0):
    return correct * 0.99 < tested < correct * 1.01


def stream_to_file(filename, stream):
    with open(filename, 'a') as outfile:
        outfile.write(stream.getvalue())


def setup_logger(logger_name, filehandler_name, capacity=50000000):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    filehandler = logging.FileHandler(filehandler_name)
    memoryhandler = logging.handlers.MemoryHandler(
                    capacity=capacity,
                    flushLevel=logging.ERROR,
                    target=filehandler
                    )

    logger.addHandler(memoryhandler)
    return logger
