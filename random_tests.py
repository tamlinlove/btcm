from btcm.bt.logger import Logger
from btcm.examples.random.random_state import RandomState
from btcm.examples.random.random_bt import random_bt
from btcm.examples.random import random_domain

def run(
        seed:int,
        num_vars:int,
        cm_connectivity:float,
        num_leaves:int,
        top_ratio:float=0.5,
        internal_ratio:float=0.25,
        itervention:str = None,
        run_name:str = "default",
        counter:int = 0,
        max_executions:int=5400,
    ):
    # Print
    print(f"{counter+1}/{max_executions}: Running random domain with seed {seed}, vars {num_vars}, connectivity {cm_connectivity}, leaves {num_leaves}, top_ratio {top_ratio}, internal_ratio {internal_ratio}, intervention {itervention}, run_name {run_name}")

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

    # Intervention
    if itervention is not None:
        board.state.flip(intervention)

    # Logger
    filename = f"logs/random/random_{run_name}_seed_{seed}_vars_{num_vars}_connectivity_{cm_connectivity}_leaves_{num_leaves}"
    logger = Logger(tree=tree, filename=filename, log_env=False)
    tree.visitors.append(logger)

    # Run the tree
    random_domain.run(tree=tree, display_tree=False)

    # Increment counter
    counter += 1
    return counter

if __name__ == "__main__":
    # Set parameters for random CMs and BTs
    num_seeds = 10
    seed_set = list(range(num_seeds))
    num_vars_set = [4,8,12]
    cm_connectivity_set = [0,0.25,0.5,0.75,1]
    top_ratio = 0.5
    internal_ratio = 0.25
    num_leaves_set = [2,4,8]

    # Counter
    counter = 0
    max_executions = int(num_seeds * len(cm_connectivity_set) * len(num_leaves_set) * (top_ratio*sum(num_vars_set) + len(num_vars_set)))

    # Execution
    for seed in seed_set:
        for num_vars in num_vars_set:
            for cm_connectivity in cm_connectivity_set:
                for num_leaves  in num_leaves_set:
                    # Default run
                    counter = run(
                        seed=seed,
                        num_vars=num_vars,
                        cm_connectivity=cm_connectivity,
                        num_leaves=num_leaves,
                        top_ratio=top_ratio,
                        internal_ratio=internal_ratio,
                        run_name="default",
                        counter=counter,
                        max_executions=max_executions,
                    )

                    num_tops = int(round(top_ratio * num_vars))
                    for var_index in range(num_tops):
                        # Run with intervention on each top variable
                        intervention = f"T{var_index+1}"
                        counter = run(
                            seed=seed,
                            num_vars=num_vars,
                            cm_connectivity=cm_connectivity,
                            num_leaves=num_leaves,
                            top_ratio=top_ratio,
                            internal_ratio=internal_ratio,
                            itervention=intervention,
                            run_name=f"T{var_index+1}",
                            counter=counter,
                            max_executions=max_executions,
                        )

