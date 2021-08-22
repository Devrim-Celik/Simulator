from security.sda_functions import *

def get_n_highest_indices(iterable, n):
    return sorted(np.array(iterable).argsort()[-n:][::-1])

def sda(file_name = "playground_experiment/packets/packets-20210822-215456.txt"):
    # TODO work CONFIG params in
    print("\n\n\n[!] STARTING SDA...")
    # load the observations and relevant ids from the simulations
    sender_id, recipient_ids, raw_observations = load_packets(file_name = file_name)

    # simplify ids and get the translation dictionary
    raw_observations, translation_dict = simplify_ids(raw_observations)
    # use it to also define the ID of the sender we want to attack
    ID_TO_TRACK = translation_dict[sender_id]
    
    # generate proper observations
    observations = extract_observations_continuous(raw_observations, 100, ID_TO_TRACK, 1/0.1, 3, 0.50)

    #### apply the attack
    ## STANDARD
    b = np.mean([np.sum(t[0]) for t in observations])
    sda_probabilities = standard_SDA(observations, b, [1/100 for _ in range(100)], ID_TO_TRACK) #TODO the 100 is hardcoded
    ## IMPROVED EXTENDED


    # compare the results vs the real recipients
    nr_recipients = len(recipient_ids)

    # get the tranlsated real recipient ids
    GOAL_IDS = sorted([translation_dict[id] for id in recipient_ids])
    # get the most likely recipients according to sda
    PREDICTED_IDS = get_n_highest_indices(sda_probabilities, nr_recipients)

    print("REAL RECIPIENTS")
    print(sorted(GOAL_IDS))
    print("PREDICTED RECIPIENTS")
    print(PREDICTED_IDS)

    return PREDICTED_IDS

if __name__=="__main__":
    sda()
