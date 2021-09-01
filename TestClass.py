from simulation_modes import test_mode
import os
from sda import sda
import time
import pickle
import json

class CollectData(object):

    def __init__(
        self,
        config_file_path = "./test_config.json",
        test_path = "./testclass_experiments",
        nr_users_range = [50, 100, 200],
        random_graph_range = [True, False],
        cover_traffic_range = [True, False],
        nr_messages = 10
    ):

        self.nr_users_range = nr_users_range
        self.random_graph_range = random_graph_range
        self.cover_traffic_range = cover_traffic_range
        self.nr_messages = nr_messages

        with open(config_file_path) as json_file:
            print(config_file_path)
            self.config = json.load(json_file)
        self.config["logging"]["enabled"] = False

        self.path = test_path + "/test_" + time.strftime("%Y%m%d-%H%M%S")

        self.test_files = []

        if not os.path.exists(test_path):
            os.makedirs(test_path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if not os.path.exists(f"{self.path}/logs"):
            os.makedirs(f"{self.path}/logs")

    def run_tests(self):

        for nr_users in self.nr_users_range:
            for rg in self.random_graph_range:
                for ct in self.cover_traffic_range:
                    # change the config
                    self.config["clients"]["number"] = nr_users
                    self.config["social_graph"]["uniform_setup"] = not rg
                    self.config["clients"]["cover_traffic"] = ct
                    self.config["misc"]["num_target_packets"] = self.nr_messages
                    # execute the run
                    file_name = test_mode.run(exp_dir=self.path, conf_file=None, conf_dic=self.config)

                    dic = {
                        "file_name": file_name,
                        "nr_users": nr_users,
                        "random_graph": rg,
                        "cover_traffic": ct,
                        "nr_messages": self.nr_messages
                    }

                    self.test_files.append(dic)

                    # save current list
                    with open(f"{self.path}/summary.pkl", 'wb') as handle:
                        pickle.dump(self.test_files, handle, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    cd = CollectData()
    cd.run_tests()
