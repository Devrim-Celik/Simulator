import numpy as np

TELEGRAM_TRANSITION_PROBABILITIES = np.array([
    [0.40, 0.47, 0.10, 0.01, 0.02], # Text
    [0.29, 0.53, 0.11, 0.02, 0.05], # Photo
    [0.19, 0.36, 0.40, 0.02, 0.03], # Video
    [0.17, 0.59, 0.13, 0.09, 0.02], # File
    [0.14, 0.40, 0.10, 0.01, 0.35]  # Audio
])

TELEGRAM_AVG_SIZES_BYTES = [
    306.61,
    91.33 * 1000,
    35.49 * 1000**2,
    52.56 * 1000,
    4.44 * 1000**2
]

class MarkovChain(object):

    def __init__(self, transition_matrix: np.ndarray, starting_state: int = 0):
        """

        Args:
            transition_matrix: contains the transition probabilities; entry
                                (i,j) gives the probability of transition from
                                state i to state j.

            starting_state: the state in which we start a random walk through
                            his Markov chain
        """
        # check for dimensionality of transition matrix
        if len(transition_matrix.shape) != 2:
            raise ValueError(f"Transition matrix should have 2 dimensions, not [{len(transition_matrix.shape)}].")

        # check that transition matrix is a square matrix
        if transition_matrix.shape[0] != transition_matrix.shape[1]:
            raise ValueError(f"Transition matrix should be a square matrix, not of dimension [{transition_matrix.shape}].")

        # check that the given starting state is within the acceptable range
        if not (0 <= starting_state < transition_matrix.shape[0]):
            raise ValueError(f"Starting state should be between {0} and {transition_matrix.shape[0]}, not [{starting_state}].")

        self.transition_matrix = transition_matrix
        self.nr_states = transition_matrix.shape[0]
        self.current_state = starting_state

    def sample(self, state: int = None) -> int:
        """
        Sample from the Markov chain and transition the state.

        Args:
            state: the current state

        Returns:
            new_state: the next state
        """
        # if not state is supplied, use the internal current state
        if not state:
            state = self.current_state
        # if one was supplied, check its value
        else:
            if not (0 <= state < transition_matrix.shape[0]):
                raise ValueError(f"Supplied state should be between {0} and {transition_matrix.shape[0]}, not [{state}].")

        # sample the Markov chain to get the new state
        new_state = np.random.choice(range(self.nr_states), p = self.transition_matrix[state, :])
        self.current_state = new_state

        return new_state

if __name__=="__main__":
    t = np.array([[0.5, 0., 0.5], [1., 0., 0.], [1/3, 1/3, 1/3]])

    mc = MarkovChain(t)

    for i in range(20):
        print(mc.current_state)
        mc.sample()
