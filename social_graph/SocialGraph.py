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
    G = np.zeros((N, N)).astype("int")

    # get clique sizes
    clique_sizes = create_clique_sizes(N, min_clique_size, max_clique_size)

    # add them to G
    G = generate_cliques(G, clique_sizes)

    return G

#### STEP 2
def generate_open_connect_attr(
    N: int,
    min_oc: int = 1,
    max_oc: int = 10,
    a: float = 2.5
) -> list:
    # draw form the power law distribution
    power_law_list = 1-np.random.power(a, N) # TODO weird that it works like this
    # scale them accordingly
    oc_values = list(np.around(power_law_list*(max_oc-min_oc) + min_oc))

    return oc_values

#### STEP 3
def merge_nodes(G: np.ndarray, indx1: int, indx2: int) -> (np.ndarray, int, int):
    # chose the name that will survive
    survivor = np.random.choice([indx1, indx2], 1)[0]
    deleted = indx1 if indx2 == survivor else indx2

    # merge the connections that go form them and to them
    merged_row = np.logical_or(G[indx1,:], G[indx2,:]).astype("int")
    merged_col = np.logical_or(G[:, indx1], G[:, indx2]).astype("int")

    # replace the old row/column with the new ones
    G[survivor,:] = merged_row
    G[:,survivor] = merged_col

    # return the merged G, as well as the index to be deleted
    return G, survivor, deleted


def oc_merging_update(open_connections, survived, deleted, strategy = "max"):
    # subtract 1, since it just got merged
    open_connections[survived] -= 1
    open_connections[deleted] -= 1

    # merge the oc values according to the specified strategy
    if strategy == "max":
        open_connections[survived] = max([open_connections[survived], open_connections[deleted]])

    # remove the oc of the deleted node, in order to not connect it
    open_connections[deleted] = 0

    return open_connections

def merge_cliques(G: np.ndarray, open_connections: list) -> np.ndarray:
    # list for saving which indices need to be deleted, because they got merged
    # with another node
    to_be_deleted = []

    # while we connect all that we could (and the rest is different, i.e.,
    # cant be connected)
    while (sum(open_connections) >= 2) and (np.nonzero(open_connections)[0].shape[0] > 1):
        # get all user indices with open connections
        choices = np.nonzero(open_connections)[0]

        # choose two of them
        u1, u2 = np.random.choice(choices, 2)

        # check that they are different
        if u1 != u2:

            # add the connections
            G, survived_indx, deleted_indx = merge_nodes(G, u1, u2)
            # update the oc connections after this merge and note the deleted
            # index
            open_connections = oc_merging_update(
                                    open_connections,
                                    survived_indx,
                                    deleted_indx
                                )
            to_be_deleted.append(deleted_indx)

    # get rid of all recurrent connections
    np.fill_diagonal(G, 0)

    # delete all merged rows/columns
    for indx in sorted(to_be_deleted, reverse=True):
        G = np.delete(G, indx, 0)
        G = np.delete(G, indx, 1)

    return G

### STEP 4
def prune_graph(G, N_to_be):

    if G.shape[0] < N_to_be:
        return False
    elif G.shape[0] == N_to_be:
        return G
    else:
        to_be_deleted = np.random.choice(list(range(G.shape[0])), size = G.shape[0] - N_to_be, replace=False)
        # delete all merged rows/columns
        for indx in sorted(to_be_deleted, reverse=True):
            G = np.delete(G, indx, 0)
            G = np.delete(G, indx, 1)

        return G

### MISC

def count_isolated(G: np.ndarray) -> int:
    """
    Counts the number of isolated groups in the topology.
    """
    # identify the largest component and the "isolated" nodes
    components = list(nx.connected_components(nx.from_numpy_matrix(G)))
    return len(components)

def switch_alice_with_user(G:np.ndarray, alice_recipient_nr:int) -> (np.ndarray, bool):
    """
    Returns:
        (np.ndarry, bool): boolean indicates if it was successful. np.ndarray
                            is None if it didnt.
    """

    # get all the indices of possible switch partners
    possible_switch_partner_indc = np.argwhere(np.sum(G, axis=1) == alice_recipient_nr)

    # check if any of those is not connected to alice; this is important since,
    # if they are connected this makes things harder (in which case we just
    # return false and try with another setup)
    switch_partner_indx = -1
    for candidate_indx in possible_switch_partner_indc:
        # if this condition triggers, than we found such a user
        if G[0, candidate_indx] == 0:
            switch_partner_indx = candidate_indx
            break
    # if we didnt find one yet, return false
    if switch_partner_indx == -1:
        return (None, False)

    ## else, switch their connections
    switch_indices = [0, switch_partner_indx]
    ## TODO this throws the deprecated numpy warning
    to_be_switched_indc = ~np.isin(list(np.arange(G.shape[0])), switch_indices)
    # get all connection but the one of alice and the partner (they stay)
    alice_connections = G[0, to_be_switched_indc].copy()
    partner_connections = G[switch_partner_indx, to_be_switched_indc].copy()
    # switch them (col and row) for alice
    G[0, to_be_switched_indc] = partner_connections
    G[to_be_switched_indc, 0] = partner_connections
    # same for the partner
    G[switch_partner_indx, to_be_switched_indc] = alice_connections
    G[to_be_switched_indc, switch_partner_indx] = alice_connections

    return G, True

### MAIN

def plot_graph_network(
    G: np.array,
    title:str = None,
    node_size: int = 5
) -> None:
    plt.figure(figsize=(10,5))

    ax = plt.gca()
    ax.set_title(title + f" | Nr. Nodes = {G.shape[0]}")

    _G = nx.from_numpy_matrix(G)
    nx.draw_spring(_G, node_color='red', ax = ax, node_size = node_size)

    _ = ax.axis('off')

    plt.show()


# TODO ==> RIGHT PARAMS?
def generate_random_social_graph(
    N: int,
    min_clique_size: int = 2,
    max_clique_size: int = 5,
    min_oc: int = 1,
    max_oc: int = 4,
    power_law_a: float = 2.5,
    alice_recipient_nr: int = None,
    plot_network: bool = False
):
    # we only want to consider networks, where there aren't any outside
    # stragglers, i.e., everybody can indirectly talk to everybody
    isolated_exists = True

    # for determining if alice has the right amount of recipients, as defined
    alice_right_nr_recipients = False

    while isolated_exists or not alice_right_nr_recipients:
        # so that they dont stack up over multiple iterations, we re-initiate
        # them every iteration
        isolated_exists = True
        alice_right_nr_recipients = False

        # start with more nodes than we actually want, since the merging process
        # will delete nodes; we will prune the rest at the end
        overestimated_N = int(N*1.5)

        # generate the cliques
        G_iso_clique =  generate_isolted_cliques(overestimated_N, min_clique_size, max_clique_size)

        # genereate open connection attributes
        open_connections = generate_open_connect_attr(overestimated_N, min_oc, max_oc, power_law_a)

        # use these to merge cliques
        G_merged = merge_cliques(G_iso_clique, open_connections)


        # pruning to the right number number of nodes
        G_pruned = prune_graph(G_merged, N)

        # check if the prune graph function threw a problem
        if (isinstance(G_pruned, bool)) and (G_pruned == False):
            continue


        ## CONDITION 1 - NO ISOLATED GROUPS: we dont isolated subgroups

        # if there are no more than one isolated graph, we are fininshed
        if count_isolated(G_pruned) == 1:
            isolated_exists = False

        ## CONDITION 2 - ALICE RECIPIENT NR: try to change the topology, such
        ## that alice has the right amount of recipients
        if alice_recipient_nr:
            # check if it already works
            if np.sum(G_pruned[0, :]) == alice_recipient_nr:
                alice_right_nr_recipients = True
            # else, check if there is some other user that has the right amount
            elif alice_recipient_nr in np.sum(G_pruned, axis=1):
                # then we change the topology (switch the users connectivity with
                # the one of alice) to make it fit
                G_pruned, alice_right_nr_recipients = switch_alice_with_user(G_pruned, alice_recipient_nr)
        else:
            alice_right_nr_recipients = True


    if plot_network:
        plot_graph_network(G_iso_clique, "After Clique Generation")
        plot_graph_network(G_merged, "After Merge")
        plot_graph_network(G_pruned, "After Pruning")

    return G_pruned

##### Uniform Social Graph
def generate_uniform_social_graph(N: int, alice_recipient_nr: int):
    """
    For generating a social graph, where everybody considers everybody a
    recipient. Alice is the exception, with a specified amount of recipients.
    Note, alice has index 0.
    """
    # create a fully connected one
    G = np.ones((N, N))

    # then set the diagonal to 0
    np.fill_diagonal(G, 0)

    # select the appropriate number of indices to set to 0
    sever_connections_indc = np.random.choice(range(1, N), size= (N-1) - alice_recipient_nr, replace = False)

    # delete these connections
    G[0, sever_connections_indc] = 0
    G[sever_connections_indc, 0] = 0

    return G

if __name__=="__main__":
    G = generate_random_social_graph(10, 3, 8, 0, 2, 2.5, 3, False)
