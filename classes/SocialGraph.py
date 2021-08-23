import networkx as nx
import numpy as np
import random

def create_clique_sizes(
    N: int,
    min_clique_size: int = 2,
    max_clique_size: int = 5
):
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

def generate_cliques(G, clique_sizes):
    # for keeeping track how many users are not in a clique yet
    unassigned_users = list(range(G.shape[0]))
    assigned_users = []

    # add the cliques
    for clique_size in clique_sizes:
        # get the right amount of random unassigned users
        clique_users = random.sample(set(unassigned_users) - set(assigned_users), clique_size)

        # add this clique
        G = add_single_clique(G, clique_users)

        # add them to the assigned users
        assigned_users.extend(clique_users)

    return G

def add_single_clique(G, clique_users):
    for c_sender in clique_users:
        for c_receiver in clique_users:
            if c_sender != c_receiver:
                G[c_sender, c_receiver] = 1
    return G


def generate_isolted_cliques(
    N: int,
    min_clique_size: int = 2,
    max_clique_size: int = 5
):
    # create an empty connection graph
    G = np.zeros((N, N))

    # get clique sizes
    clique_sizes = create_clique_sizes(N, min_clique_size, max_clique_size)
    print(clique_sizes)

    # add them to G
    G = generate_cliques(G, clique_sizes)

    return G
