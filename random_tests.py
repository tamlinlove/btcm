from btcm.examples.random.random_state import RandomState
from btcm.examples.random.random_bt import random_bt
from btcm.examples.random import random_domain

if __name__ == "__main__":
    # Set parameters for random CMs and BTs
    num_seeds = 10
    seed_set = list(range(num_seeds))
    num_vars_set = [4,8,12]
    cm_connectivity_set = [0,0.25,0.5,0.75,1]
    top_ratio = 0.5
    internal_ratio = 0.25
    num_leaves_set = [2,4,8]

    # Execution
    for seed in seed_set:
        for num_vars in num_vars_set:
            for cm_connectivity in cm_connectivity_set:
                for num_leaves  in num_leaves_set:
                    # Generate a random domain
                    board, tree = random_domain.random_domain(
                        num_vars=num_vars,
                        connectivity=cm_connectivity,
                        num_leaves=num_leaves,
                        top_ratio=top_ratio,
                        internal_ratio=internal_ratio,
                        seed=seed,
                        display=False
                    )

                    # Run the tree
                    random_domain.run(tree=tree, display_tree=True)
                    print("\n\n\n")

