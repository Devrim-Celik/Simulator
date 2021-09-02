from simulation_modes import test_mode
import os
from sda import sda
import time
import pickle
import json
import pprint
from datetime import datetime
pp = pprint.PrettyPrinter(indent=4)



class CollectData(object):

    def __init__(
        self,
        config_file_path = "./test_config.json",
        test_path = "./testclass_experiments",
        nr_users_range = [50, 100, 200, 500],
        random_graph_range = [True, False],
        cover_traffic_range = [(True, 2.5), (True, 5), (True, 10), (True, 25), (False, 1.0)], # messages per second, default is 5
        mix_avg_delay_range = [0.025, 0.05, 0.1], # avg delay in seconds, default is 50ms
        nr_messages = 1000,
        nr_simulations_per_setup = 2
    ):

        self.nr_users_range = nr_users_range
        self.random_graph_range = random_graph_range
        self.cover_traffic_range = cover_traffic_range
        self.mix_avg_delay_range = mix_avg_delay_range
        self.nr_messages = nr_messages
        self.nr_simulations_per_setup = nr_simulations_per_setup

        with open(config_file_path) as json_file:
            self.config = json.load(json_file)
        self.config["logging"]["enabled"] = False

        self.path = test_path + "/test_" + time.strftime("%Y%m%d-%H%M%S")

        self.test_files = []

        if not os.path.exists(test_path):
            os.makedirs(test_path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)


    def run_tests(self):
        for _ in range(self.nr_simulations_per_setup):
            for nr_users in self.nr_users_range:
                for rg in self.random_graph_range:
                    for ct, ct_rate in self.cover_traffic_range:
                        for avg_delay in self.mix_avg_delay_range:
                            # change the config
                            self.config["mixnodes"]["avg_delay"] = avg_delay
                            self.config["clients"]["number"] = nr_users
                            self.config["clients"]["cover_traffic"] = ct
                            self.config["clients"]["cover_traffic_rate"] = ct_rate
                            self.config["social_graph"]["uniform_setup"] = not rg
                            self.config["misc"]["num_target_packets"] = self.nr_messages

                            ct_rate_str = str(ct_rate).replace(".", "dot")
                            avg_delay_str = str(avg_delay).replace(".", "dot")
                            folder_name = f"{nr_users}_{not rg}_{ct}_{ct_rate_str}_{avg_delay_str}_{self.nr_messages}"
                            folder_path = (self.path + "/" + folder_name)

                            if not os.path.exists(folder_path):
                                os.makedirs(folder_path)

                            if not os.path.exists(f"{folder_path}/logs"):
                                os.makedirs(f"{folder_path}/logs")

                            start_time = datetime.now()
                            # execute the run
                            file_name = test_mode.run(exp_dir=folder_path, conf_file=None, conf_dic=self.config)
                            end_time = datetime.now()

                            total_runtime = (end_time-start_time).seconds

                            dic = {
                                "file_name": file_name,
                                "sub_folder": folder_name,
                                "nr_users": nr_users,
                                "random_graph": rg,
                                "cover_traffic": (ct, ct_rate),
                                "mix_avg_delay": avg_delay,
                                "nr_messages": self.nr_messages,
                                "runtime": total_runtime
                            }

                            self.test_files.append(dic)

                            # save current list
                            with open(f"{self.path}/summary.pkl", 'wb') as handle:
                                pickle.dump(self.test_files, handle, protocol=pickle.HIGHEST_PROTOCOL)


class SDACollector(object):

    def __init__(
        self,
        test_path,
        chernov_conf_range = [0.5, 0.75, 0.90],
        use_social_graph_range = [True, False],
        config_file_path = "./test_config.json"
    ):

        self.chernov_conf_range = chernov_conf_range
        self.use_social_graph_range = use_social_graph_range
        self.test_path = test_path

        with open(test_path + "/summary.pkl", "rb") as f:
            self.summary = pickle.load(f)
        with open(config_file_path) as json_file:
            self.config = json.load(json_file)

        self.result_summary = []

    def run_tests(self):
        for dic in self.summary:
            for confidence in self.chernov_conf_range:
                for usg in self.use_social_graph_range:
                    # parameters for the attack
                    self.config["clients"]["number"] = dic["nr_users"]
                    self.config["social_graph"]["uniform_setup"] = not dic["random_graph"]
                    self.config["misc"]["num_target_packets"] = dic["nr_messages"]
                    self.config["clients"]["cover_traffic"] = dic["cover_traffic"]
                    self.config["mixnodes"]["avg_delay"] = dic["mix_avg_delay"]
                    self.config["security"]["use_social_graph"] = usg
                    self.config["security"]["chernov_confidence"] = confidence

                    # parameters for saving the results later
                    temp_dic = dic.copy()
                    temp_dic["chernov_confidence"] = confidence
                    temp_dic["use_social_graph"] =usg


                    temp_dic["sda_result"] = sda(dic["file_name"], config_dic = self.config, over_time = True)

                    self.result_summary.append(temp_dic)

                    # save current list
                    with open(f"{self.test_path}/result_summary.pkl", 'wb') as handle:
                        pickle.dump(self.result_summary, handle, protocol=pickle.HIGHEST_PROTOCOL)
        pp.pprint(self.result_summary)

if __name__ == "__main__":
    cd = CollectData()
    cd.run_tests()

    sdac = SDACollector(cd.path)
    sdac.run_tests()
