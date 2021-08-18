from sda_functions import *

if __name__=="__main__":
    # work CONFIG params in

    # load the observations from the simulations
    F1 = "playground_experiment/packets/packets-20210818-013834.txt"
    F2 = "playground_experiment/packets/packets-20210818-030325.txt"
    raw_observations =  load_packets(file_name = F2)
    # simplify ids
    raw_observations = simplify_ids(raw_observations)

    ID_TO_TRACK = 5

    observations = extract_observations_continuous(raw_observations, 100, ID_TO_TRACK, 1/0.1, 3, 0.50)

    b = np.mean([np.sum(t[0]) for t in observations])
    print(standard_SDA(observations, b, [1/100 for _ in range(100)], ID_TO_TRACK))
