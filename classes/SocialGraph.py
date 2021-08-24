import networkx as nx
import numpy as np
import random
import matplotlib.pyplot as plt

def create_clique_sizes(
    N: int,
    min_clique_size: int = 2,
    max_clique_size: int = 5
) -> list:
    """
    Determine the sizes of each clique, such that they are all within the given
    bound and sum up to N.
    """
    # create a list of the clique sizes
    clique_sizes = []

    # fill them random until we can no longer trust the random extensions
    # to guarantee to exactly sum up to N while mainting the given interval
    # of values
    while sum(clique_sizes) < (N - max_clique_size - min_clique_size):
        clique_sizes.append(random.randint(min_clique_size, max_clique_size))

    # fill the rest manually
    if (N - sum(clique_sizes)) <= max_clique_size:
        # if adding one suffices
        clique_sizes.append(N - sum(clique_sizes))
    else:
        # if two are needed
        clique_sizes.extend([N - sum(clique_sizes) - min_clique_size, min_clique_size])

    return clique_sizes

def generate_cliques(G: np.ndarray, clique_sizes: list) -> np.ndarray:
    # for keeeping track how many users are not in a clique yet
    unassigned_users = list(range(G.shape[0]))
    assigned_users = []

    # add the cliques
    for clique_size in clique_sizes:
        # get the right amount of random unassigned users
        clique_users = random.sample(set(unassigned_users) - set(assigned_users), clique_size)

        # add this clique
        G = add_clique(G, clique_users)

        # add them to the assigned users
        assigned_users.extend(clique_users)

    return G

def add_clique(G: np.ndarray, clique_users: list) -> np.ndarray:
    for c_sender in clique_users:
        for c_receiver in clique_users:
            if c_sender != c_receiver:
                G[c_sender, c_receiver] = 1
    return G

def generate_isolted_cliques(
    N: int,
    min_clique_size: int = 2,
    max_clique_size: int = 5
) -> np.ndarray:
    # create an empty connection graph
    G = np.zeros((N, N))

    # get clique sizes
    clique_sizes = create_clique_sizes(N, min_clique_size, max_clique_size)

    # add them to G
    G = generate_cliques(G, clique_sizes)

    return G

#### STEP 2
def generate_open_connect_attr(
    N: int,
    min_oc: int = 1,
    max_oc: int = 4,
    a: int = 5
) -> list:
    return list((np.random.power(a, N)*max_oc + min_oc).astype("int"))

#### STEP 3
def merge_cliques(G: np.ndarray, open_connections: list) -> np.ndarray:
    #TODO we dont merge, but we connect

    # while we connect all that we could (and the rest is different, i.e.,
    # cant be connected)
    while (sum(open_connections) >= 2) and (np.nonzero(open_connections)[0].shape[0] > 1):
        # get all user indices with open connections
        choices = np.nonzero(open_connections)[0]

        # choose two of them
        u1, u2 = np.random.choice(choices, 2)

        # check that they are different
        if u1 != u2:

            # subtract their corresponding values
            open_connections[u1] -= 1
            open_connections[u2] -= 1

            # add the connections
            G[u1, u2] = 1
            G[u2, u1] = 1

    return G

###
def generate_social_graph(
    N: int,
    min_clique_size: int = 2,
    max_clique_size: int = 5,
    min_oc: int = 1,
    max_oc: int = 4,
    plot_network: bool = False
):
    # generate the cliques
    G =  generate_isolted_cliques(N, min_clique_size, max_clique_size)

    # genereate open connection attributes
    open_connections = generate_open_connect_attr(N, min_oc, max_oc)

    # use these to merge cliques
    G = merge_cliques(G, open_connections)

    if plot_network:
        _G = nx.from_numpy_matrix(G)
        nx.draw_spring(_G, node_size = 5)
        plt.show()

    return G


if __name__=="__main__":
    G = generate_social_graph(100, 3, 5, 0, 2, True)
