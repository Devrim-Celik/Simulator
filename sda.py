from security.sda_functions import *
import json

def get_n_highest_indices(iterable, n):
    return sorted(np.array(iterable).argsort()[-n:][::-1])

def sda(
    file_name = "playground_experiment/packets/packets-20210830-005742.txt",
    config_file = "test_config.json",
    config_dic = None,
    over_time = False
):
    # TODO work CONFIG params in
    print("\n\n\n[!] STARTING SDA...")

    # load config
    if config_dic:
        conf = config_dic
    else:
        with open(config_file, "rb") as f:
            conf = json.load(f)

    # load the observations and relevant ids from the simulations
    sender_id, recipient_ids, sending_probabilities, raw_observations = load_packets(file_name = file_name)

    # simplify ids and get the translation dictionary
    raw_observations, translation_dict = simplify_ids(raw_observations)
    # use it to also define the ID of the sender we want to attack
    ID_TO_TRACK = translation_dict[sender_id]

    # generate proper observations
    # TODO we use the real mu, not an estimation
    observations = extract_observations_continuous(
        raw_observations,
        conf["clients"]["number"],
        ID_TO_TRACK,
        1/conf["mixnodes"]["avg_delay"],
        conf["network"]["stratified"]["layers"],
        conf["security"]["chernov_confidence"]
    )

    #### apply the attack
    b = np.mean([np.sum(t[0]) for t in observations])
    ## STANDARD
    if conf["security"]["use_social_graph"]:
        # here we use information about the social graph, i.e., the probabilites
        # create the sending profile of the other users by excluding alice
        # and summing over the rows
        background_profile_temp = list(np.sum(sending_probabilities[1:], axis=0))
        # normalize
        background_profile = background_profile_temp/np.sum(background_profile_temp)
    else:
        background_profile = [1/conf["clients"]["number"] for _ in range(conf["clients"]["number"])]

    # compare the results vs the real recipients
    nr_recipients = len(recipient_ids)

    # get the tranlsated real recipient ids
    GOAL_IDS = sorted([translation_dict[id] for id in recipient_ids])

    if over_time:
        accuracies = SDA_over_time(observations, b, background_profile, GOAL_IDS, ID_TO_TRACK)
        return accuracies
    else:
        sda_probabilities = standard_SDA(observations, b, background_profile, ID_TO_TRACK)

        ## IMPROVED EXTENDED
        #sda_probabilities = improv_extended_SDA(observations, b, ID_TO_TRACK)


        # get the most likely recipients according to sda
        PREDICTED_IDS = get_n_highest_indices(sda_probabilities, nr_recipients)

        print("\nREAL RECIPIENTS")
        print(sorted(GOAL_IDS))
        print("PREDICTED RECIPIENTS")
        print(PREDICTED_IDS)

        return PREDICTED_IDS

if __name__=="__main__":
    sda()
