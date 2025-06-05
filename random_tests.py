from btcm.examples.random.random_state import RandomState

if __name__ == "__main__":
    # Set parameters for random CMs and BTs
    num_seeds = 10
    seed_set = list(range(num_seeds))
    num_vars_set = [4,8,12]
    cm_connectivity_set = [0,0.25,0.5,0.75,1]
    top_ratio = 0.5
    num_leaves_set = [2,4,8]
    num_composites_set = [1,4,8]

    # Start by generating ground truth state models
    for seed in seed_set:
        for num_vars in num_vars_set:
            for cm_connectivity in cm_connectivity_set:
                # Generate a random CM
                state = RandomState(
                    num_vars=num_vars,
                    connectivity=cm_connectivity,
                    top_ratio=top_ratio,
                    seed=seed
                )