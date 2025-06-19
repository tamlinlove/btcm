import os
import csv

from btcm.bt.btstate import BTStateManager
from btcm.cfx.comparer import Comparer
from btcm.examples.random.random_domain import reconstruct_random_tree,make_state,state_class

def load_runs(directory):
    runs = {}
    for filename in os.listdir(directory):
        flist = filename.split("_")
        run_name = flist[1]
        seed = int(flist[3])
        num_vars = int(flist[5])
        cm_connectivity = float(flist[7])
        num_leaves = int(flist[9].split(".")[0])

        if seed not in runs:
            runs[seed] = {}
        if num_vars not in runs[seed]:
            runs[seed][num_vars] = {}
        if cm_connectivity not in runs[seed][num_vars]:
            runs[seed][num_vars][cm_connectivity] = {}
        if num_leaves not in runs[seed][num_vars][cm_connectivity]:
            runs[seed][num_vars][cm_connectivity][num_leaves] = {}
        if run_name not in runs[seed][num_vars][cm_connectivity][num_leaves]:
            runs[seed][num_vars][cm_connectivity][num_leaves][run_name] = None
        runs[seed][num_vars][cm_connectivity][num_leaves][run_name] = filename
    return runs


if __name__ == "__main__":
    # Load all runs into a dictionary
    runs = load_runs("logs/random/")

    # Comparison parameters
    max_follow_ups = 2
    # max_depth = 2
    visualise = False
    visualise_only_valid = False
    hide_display = True

    save_data = []

    particular_execution = False
    ped = {
        "seed":3,
        "num_vars":12,
        "connectivity":0.5,
        "num_leaves":8,
        "target":"T3",
    }

    if particular_execution:
        hide_display = False
    
    # Run comparison
    for seed in runs:
        for num_vars in runs[seed]:
            for cm_connectivity in runs[seed][num_vars]:
                for num_leaves in runs[seed][num_vars][cm_connectivity]:
                    if particular_execution:
                        if not(seed == ped["seed"] and num_vars == ped["num_vars"] and cm_connectivity == ped["connectivity"] and num_leaves == ped["num_leaves"]):
                            continue
                    print(f"Seed: {seed}, Num Vars: {num_vars}, Connectivity: {cm_connectivity}, Num Leaves: {num_leaves}")
                    
                    default_file = runs[seed][num_vars][cm_connectivity][num_leaves]["default"]
                    other_changes = [f for f in runs[seed][num_vars][cm_connectivity][num_leaves] if f != "default"]
                    
                    for change in other_changes:
                        if particular_execution:
                            if change != ped["target"]:
                                continue
                                

                        change_file = runs[seed][num_vars][cm_connectivity][num_leaves][change]
                        print(f"\tComparing {default_file} with {change_file}")

                        # Initialise managers
                        manager1 = BTStateManager(
                            default_file, 
                            directory="logs/random", 
                            reconstruct_func=reconstruct_random_tree,
                            make_state_func=make_state,
                            state_class_func=state_class,
                            no_env=True,
                        )
                        manager2 = BTStateManager(
                            change_file, 
                            directory="logs/random", 
                            reconstruct_func=reconstruct_random_tree,
                            make_state_func=make_state,
                            state_class_func=state_class,
                            no_env=True,
                        )

                        # Initialise comparer
                        comparer = Comparer(manager1,manager2)

                        # Compare
                        target_var = change
                        found,depth,num_exps,num_cm_nodes,msg = comparer.explain_follow_ups(
                            target_var=target_var,
                            max_follow_ups=max_follow_ups,
                            max_depth=num_vars,
                            visualise=visualise,
                            visualise_only_valid=visualise_only_valid,
                            hide_display=hide_display
                        )

                        # Save
                        save_data.append(
                            {
                                "seed":seed,
                                "num_vars":num_vars,
                                "cm_connectivity":cm_connectivity,
                                "num_leaves":num_leaves,
                                "change":change,
                                "found":found,
                                "depth":depth,
                                "num_explanations":num_exps,
                                "num_cm_nodes":num_cm_nodes,
                                "msg":msg,
                            }
                        )

    # Save data
    if not particular_execution:
        csv_file = f'results/results_random.csv'
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=list(save_data[0].keys()))
            writer.writeheader()
            writer.writerows(save_data)

                        
                        