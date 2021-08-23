from __future__ import annotations
import typing

import numpy as np

### UTILITIES
def load_packets(file_name = "playground_experiment/packets/packets-20210818-013834.txt"):
    with open(file_name, "r") as outfile:
        pkt_list_str = outfile.readlines()
    # get sender id
    sender_id = pkt_list_str[0][:-1] # -1 for dropping \n
    # get recipient ids
    recipient_ids = eval(pkt_list_str[1])
    # get packets
    pkt_list = [eval(dic_str) for dic_str in pkt_list_str[2:]]
    return sender_id, recipient_ids, pkt_list

def simplify_ids(pkt_list):
    # get unique IDs and sort them alphabetically
    old_ids = sorted(list(set([pkt["src"] for pkt in pkt_list])))
    # generate new ids
    new_ids = list(range(len(old_ids)))

    translation_dict = {old:new for (old, new) in zip(old_ids, new_ids)}

    for pkt_dic in pkt_list:
        pkt_dic["src"] = translation_dict[pkt_dic["src"]]
        pkt_dic["dst"] = translation_dict[pkt_dic["dst"]]

    return pkt_list, translation_dict

### CHERNOV BOUND
def chernov_bound_erlang(mu, n, confidence) -> float:
    """
    Calculate the one-sided chernov bound, where the delay is sampled from
    an erlang distribution (i.e., sum of idential exponential distributions).
    """

    # calculate the appropriate parameter k
    k = np.sqrt(1/(1-confidence) - 1)

    # use this and the distribution parameters to determine the upper bound on
    # the delay
    upper_delay_bound = (k * np.sqrt(n) + n)/mu

    return upper_delay_bound

### OBSERVATION EXTRACTION
def extract_observations_continuous(pkt_list, nr_clients, id_nr_to_track, mu, n, confidence):
    """
    Extract observations for simulation where continuous mix node types were
    used.
    """
    # for saving the observations of rounds
    round_observations = []

    # extract the packets sent by the id_nr we are interested in
    pkts_of_interest = [pkt for pkt in pkt_list if pkt["src"] == id_nr_to_track]

    # calculate the upper bound on the delay we allow
    upper_delay_bound = chernov_bound_erlang(mu, n, confidence)

    # calculating the percentage of packets below the bound
    print(f"Upper Bound with {confidence*100}% Confidence is: {upper_delay_bound}.")
    under_bound_bool = []
    for indx, pkt in enumerate(pkt_list):
        delay = pkt["time_delivered"]-pkt["time_sent"]
        under_bound_bool.append(delay <= upper_delay_bound)
    print(f"{np.mean(under_bound_bool)*100}% of message delays are below that bound.")

    # for each of these packets
    for pkt_of_interest in pkts_of_interest:
        # for collecting the number of sent/received packets per round
        sent_list = [0 for _ in range(nr_clients)]
        received_list = [0 for _ in range(nr_clients)]

        # extract the time at which the packet enters the communicaton system
        t = pkt_of_interest["time_sent"]

        # go through all packets
        for pkt in pkt_list:
            ### SENT
            if t - upper_delay_bound <= pkt["time_sent"] <= t + upper_delay_bound:#
                sent_list[pkt["src"]] += 1
            ### RECEIVED
            if t <= pkt["time_delivered"] <= t + upper_delay_bound:
                received_list[pkt["dst"]] += 1

        # after having gone through all packets, add this round to the
        # observation list as a tuple of lists
        round_observations.append((sent_list, received_list))

    return round_observations

### UTILITIES
def get_probable_recipients(
    value_vector: nd.array,
    nr_recipients: int
) -> nd.array:
    """
    The results of the SDA is a vector of values, where higher values represent
    higher chances of being one of alice's recipients. This function determines
    for a given value vector and a number of recipients the indexes of these
    possible recipients (sorted by indexes).
    """

    return sorted(np.argsort(value_vector)[::-1][:nr_recipients])

def accuracy(
    real_recipients: list,
    sda_recipients: list
) -> nd.array:
    """
    Calculates the percentage of identical values between two lists.
    """
    return np.mean([int(r == s) for (r,s) in zip(real_recipients, sda_recipients)])

### SDAs

def get_SDA_b(
    round_observations: typing.List[typing.Tuple[typing.List, typing.List]],
    config: dict
) -> float:
    """
    In the typical SDA setting, b denotes the amount of messages that enter
    the anonymous communication system each round. Depending on the exact
    type of mix-node that was used, extracting this paramter differentiates.
    """
    if config["mix_type"] == "thresh":
        b = config["thresh_mix_configuration"]["threshold"]
    elif config["mix_type"] == "pool":
        b = config["pool_mix_configuration"]["N"]
    elif config["mix_type"] == "stopandgo":
        b = np.mean([np.sum(t[0]) for t in round_observations])
    return b


def standard_SDA(
    observation_list,
    b: float,
    u: list,
    alice_indx: int = 0
):
    """
    Standard statistical disclosure attack.

    Args:
        observation_list (list): each element is a tuple
                        * sender counts
                        * recipient counts
                        of one round
        b (float): number of messages per round
        u (list): other sender profile
        alice_indx (int): client index of alice, i.e., target
    """
    # get all the recipient count of the rounds, where alice is involved
    relevant_observations = [np.array(t[1]) for t in observation_list if t[0][alice_indx] >= 1]

    # make u to a numpy array
    u = np.array(u)

    # calculate the sender profile of alice
    v = b*np.sum(relevant_observations, axis=0)/len(observation_list) - (b-1)*u

    return v

def p_alice_criteria(sender_obsv, cloak_users):
    """
    Check if one of the cloak users was an active sender in a particular round.
    """
    senders = [i for i, e in enumerate(sender_obsv) if (e != 0)]

    return set(senders) & set(cloak_users)

def improv_extended_SDA(
    observation_list,
    b: float,
    alice_indx: int = 0
):
    """
    Improv-Extended statistical disclosure attack.

    Args:
        observation_list (list): each element is a tuple
                        * sender counts
                        * recipient counts
                        of one round
        b (float): number of messages per round
        alice_indx (int): client index of alice, i.e., target
    """
    # TODO non_alice_observations are empty --> chernov bound problem?
    # divide the observations
    alice_observations = [t[0] for t in observation_list if t[0][alice_indx] >= 1]
    non_alice_observations = [t[0] for t in observation_list if t[0][alice_indx] == 0]

    # get the cloak users
    alice_cloak = []
    for sender_obsv in alice_observations:
        # get all the indices of one alice rounds (excluding alices index)
        alice_cloak.extend([i for i, e in enumerate(sender_obsv) if (e != 0) and (i != alice_indx)])
    # remove the doubles and sort
    alice_cloak = sorted(list(set(alice_cloak)))

    # get all the rounds where alice did not participate, but at least one
    # of the alice's cloak
    p_alice = [obsv for obsv in non_alice_observations if p_alice_criteria(obsv, alice_cloak)]

    # calculate cloak bar
    cloak_bar_alice = np.sum(p_alice, axis=0)/len(p_alice)

    # calculate v
    t_prime = len(alice_observations)
    a_bar = np.sum([obsv[alice_indx]/np.sum(obsv) for obsv in alice_observations])/t_prime
    v = (b/(a_bar * t_prime))*np.sum(alice_observations, axis=0) - ((b-a_bar)/a_bar)*cloak_bar_alice

    return v

def SDA_over_time(
    observation_list,
    b: float,
    u: list,
    real_recipients: list,
    alice_indx: int = 0
) -> list:
    """
    Since it is also interesting to see, not only how well an SDA attack worked
    after a long simulation, but also how the accuracy of the attack developed
    over time, this function runs through parts of the simulation and applies
    the standard SDA on them.
    """
    accuracies_over_time = []

    for t_indx in range(len(observation_list)):
        # get the v vector of SDA
        v = standard_SDA(observation_list[:t_indx+1], b, u, alice_indx)
        # extract most likely recipients according to it
        sda_recipients = get_probable_recipients(v, len(real_recipients))
        # append the accuracy
        accuracies_over_time.append(accuracy(real_recipients, sda_recipients))

    return accuracies_over_time

# TODO SDAs:
# - Cloack SDA from Statistical Disclosure: Improved, Extended, and Resisted
