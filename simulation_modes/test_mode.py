import simpy
import os
import datetime
import numpy as np
from collections import namedtuple
from pathlib import Path
import pickle
import time

import experiments.Settings

from social_graph.SocialGraph import generate_random_social_graph, generate_uniform_social_graph

from classes.Net import *
from classes.Client import *
from classes.Net import *
from classes.Utilities import *
from classes.Utilities import *


throughput = 0.0

def get_loggers(log_dir, conf):

    packet_logger = setup_logger('simulation.packet', os.path.join(log_dir, 'packet_log.csv'))
    packet_logger.info(StructuredMessage(metadata=("Type", "CurrentTime", "ClientID", "PacketID", "PacketType", "MessageID", "PacketTimeQueued", "PacketTimeSent", "PacketTimeDelivered", "TotalFragments", "PrOthers", "PrSenderA", "PrSenderB", "RealSenderLabel", "Route", "PoolSizes")))

    message_logger = setup_logger('simulation.messages', os.path.join(log_dir, 'message_log.csv'))
    message_logger.info(StructuredMessage(metadata=("Type", "CurrentTime", "ClientID", "MessageID", "NumPackets", "MsgTimeQueued", "MsgTimeSent", "MsgTimeDelivered", "MsgTransitTime", "MsgSize", "MsgRealSender")))

    entropy_logger = setup_logger('simulation.mix', os.path.join(log_dir, 'last_mix_entropy.csv'))
    entropy_logger.info(StructuredMessage(metadata=tuple(['Entropy'+str(x) for x in range(int(conf["misc"]["num_target_packets"]))])))

    return (packet_logger, message_logger, entropy_logger)

def setup_env(conf):
    env = simpy.Environment()
    env.stop_sim_event = env.event()
    env.message_ctr = 0
    env.total_messages_sent = 0
    env.total_messages_received = 0
    env.finished = False
    env.entropy = numpy.zeros(int(conf["misc"]["num_target_packets"]))
    env.collected_packets = []
    return env

def run_client_server(env, conf, net, sending_probabilities, loggers):
    clients = net.clients
    print("Number of active clients: ", len(clients))

    # create the translation dictionaries
    id_to_nr, nr_to_id = translation_dictionaries(clients, clients[0].id)
    net.mixnodes[0].verbose = True

    # For Alice
    Alice = clients[0]
    Alice.label = 1
    Alice.verbose = True
    print("Alice: ", Alice.id, id_to_nr[Alice.id])
    alice_recipients, alice_recipients_probalities = get_recipients(clients, Alice.id, sending_probabilities, id_to_nr)
    env.process(Alice.start())
    env.process(Alice.start_loop_cover_traffc())

    # go through all clients, but skip Alice
    ctr = 0
    for c_indx, c in enumerate(clients[1:]):
        c.verbose = True
        # identify the recipients of alice:
        if c in alice_recipients:
            ctr += 1
            print(f"Target Recipient {ctr}: ", c.id, id_to_nr[c.id])
            c.set_start_logs()
        env.process(c.start())
        env.process(c.start_loop_cover_traffc())

    print("---------" + str(datetime.datetime.now()) + "---------")
    print("> Running the system for %s ticks to prepare it for measurment." % (conf["phases"]["burnin"]))

    # env.process(progress_update(env, 5))
    time_started = env.now
    time_started_unix = datetime.datetime.now()
    # ------ RUNNING THE STARTUP PHASE ----------
    if conf["phases"]["burnin"] > 0.0:
        env.run(until=conf["phases"]["burnin"])
    print("> Finished the preparation")

    # Start logging since system in steady state
    for p in net.mixnodes:
        p.mixlogging = True

    # start creating packets
    env.process(Alice.simulate_adding_packets_into_buffer(alice_recipients, alice_recipients_probalities))
    for c in clients[1:]:
        env.process(c.simulate_adding_packets_into_buffer(*get_recipients(clients, c.id, sending_probabilities, id_to_nr)))

    print("> Started sending traffic for measurments")

    # reste packet list
    env.collected_packets = []

    env.run(until=env.stop_sim_event)  # Run until the stop_sim_event is triggered.
    print("> Main part of simulation finished. Starting cooldown phase.")

    print("> Saving collected packets...")

    packet_folder_path = "playground_experiment/packets"
    Path(packet_folder_path).mkdir(exist_ok=True)

    pkt_list_gen = env.collected_packets
    pkt_list_info = [{"src": str(pkt.real_sender.id), "dst": str(pkt.dest.id), "time_sent": pkt.time_sent, "time_delivered": pkt.time_delivered} for pkt in pkt_list_gen]

    file_name = packet_folder_path + "/packets-" + time.strftime("%Y%m%d-%H%M%S") + ".txt"
    with open(file_name, 'w') as file_handler:
        # write the id of the sender
        file_handler.write("{}\n".format(Alice.id))
        # write the id of the recipients
        file_handler.write("[\"{}\"]\n".format("\",\"".join([r.id for r in alice_recipients])))
        # save the sending probabilities
        file_handler.write("[{}]\n".format(",".join(["[{}]".format(",".join([str(nr) for nr in sending_probabilities[sender_nr]])) for sender_nr in range(sending_probabilities.shape[0])])))
        for item in pkt_list_info:
            file_handler.write("{}\n".format(item))

    print("> Done!")

    # Log entropy
    loggers[2].info(StructuredMessage(metadata=tuple(env.entropy)))
    # ------ RUNNING THE COOLDOWN PHASE ----------
    env.run(until=env.now + conf["phases"]["cooldown"])

    # Log entropy
    loggers[2].info(StructuredMessage(metadata=tuple(env.entropy)))

    print("> Cooldown phase finished.")
    time_finished = env.now
    time_finished_unix = datetime.datetime.now()
    # print("Reciever received: ", recipient.num_received_packets)
    print("> Total Simulation Time [in ticks]: " + str(time_finished-time_started) + "---------")
    print("> Total Simulation Time [in unix time]: " + str(time_finished_unix-time_started_unix) + "---------")

    flush_logs(loggers)


    global throughput
    throughput = float(env.total_messages_received) / float(time_finished-time_started)

    mixthroughputs = []
    for m in net.mixnodes:
        mixthroughputs.append(float(m.pkts_sent) / float(time_finished-time_started))

    print("Total number of packets which went through the network: ", float(env.total_messages_received))
    print("Network throughput %f / second: " % throughput)
    print("Average mix throughput %f / second, with std: %f" % (np.mean(mixthroughputs), np.std(mixthroughputs)))

    return file_name

def flush_logs(loggers):
    for l in loggers:
        for h in l.handlers:
            h.flush()


def run(exp_dir, conf_file=None, conf_dic=None):
    print("The experiment log directory is: %s" %exp_dir)

    # Upload config file
    if conf_file:
        print("The config file is at:%s" %conf_file)
        conf = experiments.Settings.load(conf_file)
    elif conf_dic:
        conf = conf_dic
    else:
        print("A configuration dictionary or file required")

    # -------- timing for how long to run the simulation ----------
    limittime = conf["phases"]["burnin"] + conf["phases"]["execution"] # time after which we should terminate the target senders from sending
    simtime = conf["phases"]["burnin"] +  conf["phases"]["execution"] + conf["phases"]["cooldown"] # time after which the whole simulator stops

    # Logging directory
    log_dir = os.path.join(exp_dir,conf["logging"]["dir"])
    # Setup environment
    env = setup_env(conf)

    print("> Create Social Graph")
    # create the social graph
    if conf["social_graph"]["uniform_setup"]: # uniform setup
        connectivity_matrix = generate_uniform_social_graph(
                                conf["clients"]["number"],
                                conf["social_graph"]["nr_alice_recipients"]
                                )
    else: # random setup
        connectivity_matrix = generate_random_social_graph(
                                conf["clients"]["number"],
                                conf["social_graph"]["min_clique_size"],
                                conf["social_graph"]["max_clique_size"],
                                conf["social_graph"]["min_open_connections"],
                                conf["social_graph"]["max_open_connections"],
                                conf["social_graph"]["power_law_a"],
                                conf["social_graph"]["nr_alice_recipients"]
                                )
    # translate them to probabilities
    sending_probabilities = connectivity_to_probabilities(connectivity_matrix)
    
    # Create the network
    type = conf["network"]["topology"]
    loggers = get_loggers(log_dir, conf)
    net = Network(env, type, conf, loggers)

    return run_client_server(env, conf, net, sending_probabilities, loggers)
