import csv
import os
import pandas as pd

RESULT_DIR = "results/"
COMPILED_DIR = RESULT_DIR + "compiled/"

def compile_cog_seq_results():
    profiles = ["frustrated","no_attention","no_reactivity","no_memory"]

    # Read all csvs into pandas dfs
    dfs = {}
    for profile in profiles:
        filepath = f"{RESULT_DIR}results_default_{profile}.csv"
        dfs[profile] = pd.read_csv(filepath)

    # Compile into table
    table_data = []
    for profile in profiles:
        df = dfs[profile]
        # Numbers
        num_found = df['found'].sum() # Type 1: Found
        num_no_diff = df[df['msg'] == "NoDiff"].shape[0] # Type 2: No Difference
        num_other = df[df['msg'] == "Unknown"].shape[0] # Type 3: No Causal Link or Type 4: Noise Interference

        # Target recovery rate
        filtered_df = df[df['msg'] != "NoDiff"]
        true_found_count = filtered_df['found'].sum()
        total_rows = len(filtered_df)
        target_recovery_rate = (true_found_count / total_rows)

        found_df = df[df['found']]
        # Depth information
        min_depth = found_df['depth'].min()
        max_depth = found_df['depth'].max()
        avg_depth = found_df['depth'].mean()

        # NumExps information
        min_num_exps = found_df['num_explanations'].min()
        max_num_exps = found_df['num_explanations'].max()
        avg_num_exps = found_df['num_explanations'].mean()

        table_data.append(
            {
                "profile":profile,
                "num_found":num_found,
                "num_no_diff":num_no_diff,
                "num_other":num_other,
                "target_recovery_rate":target_recovery_rate,
                "min_depth":min_depth,
                "max_depth":max_depth,
                "avg_depth":avg_depth,
                "min_num_exps":min_num_exps,
                "max_num_exps":max_num_exps,
                "avg_num_exps":avg_num_exps,
            }
        )

    # Aggregated
    compiled_df = pd.concat(dfs.values(), ignore_index=True)
    # Numbers
    num_found = compiled_df['found'].sum() # Type 1: Found
    num_no_diff = compiled_df[compiled_df['msg'] == "NoDiff"].shape[0] # Type 2: No Difference
    num_other = compiled_df[compiled_df['msg'] == "Unknown"].shape[0] # Type 3: No Causal Link or Type 4: Noise Interference

    # Target recovery rate
    filtered_df = compiled_df[compiled_df['msg'] != "NoDiff"]
    true_found_count = filtered_df['found'].sum()
    total_rows = len(filtered_df)
    target_recovery_rate = (true_found_count / total_rows)

    found_df = compiled_df[compiled_df['found']]
    # Depth information
    min_depth = found_df['depth'].min()
    max_depth = found_df['depth'].max()
    avg_depth = found_df['depth'].mean()

    # NumExps information
    min_num_exps = found_df['num_explanations'].min()
    max_num_exps = found_df['num_explanations'].max()
    avg_num_exps = found_df['num_explanations'].mean()

    table_data.append(
        {
            "profile":"All",
            "num_found":num_found,
            "num_no_diff":num_no_diff,
            "num_other":num_other,
            "target_recovery_rate":target_recovery_rate,
            "min_depth":min_depth,
            "max_depth":max_depth,
            "avg_depth":avg_depth,
            "min_num_exps":min_num_exps,
            "max_num_exps":max_num_exps,
            "avg_num_exps":avg_num_exps,
        }
    )


    # Save table data
    csv_file = f'{COMPILED_DIR}results_cog_seq.csv'
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(table_data[0].keys()))
        writer.writeheader()
        writer.writerows(table_data)


def compile_random_results():
    df = pd.read_csv(f"{RESULT_DIR}results_random.csv")
    
    num_vars_set = df['num_vars'].unique()
    connectivity_set = df['cm_connectivity'].unique()
    num_leaves_set = df['num_leaves'].unique()

    table_data = []
    for num_vars in sorted(num_vars_set):
        for connectivity in sorted(connectivity_set):
            for num_leaves in sorted(num_leaves_set):
                filtered_df = df[(df['num_vars'] == num_vars) & (df['cm_connectivity'] == connectivity) & (df['num_leaves'] == num_leaves)]

                num_found = filtered_df['found'].sum() # Type 1: Found
                num_no_diff = filtered_df[filtered_df['msg'] == "NoDiff"].shape[0] # Type 2: No Difference
                num_other = filtered_df[filtered_df['msg'] == "Unknown"].shape[0] # Type 3: No Causal Link or Type 4: Noise Interference

                diff_df = filtered_df[filtered_df['msg'] != "NoDiff"]
                true_found_count = diff_df['found'].sum()
                total_rows = len(diff_df)
                target_recovery_rate = (true_found_count / total_rows)

                found_df = filtered_df[filtered_df['found']]
                # Depth information
                min_depth = found_df['depth'].min()
                max_depth = found_df['depth'].max()
                avg_depth = found_df['depth'].mean()

                # NumExps information
                min_num_exps = found_df['num_explanations'].min()
                max_num_exps = found_df['num_explanations'].max()
                avg_num_exps = found_df['num_explanations'].mean()

                table_data.append(
                    {
                        "num_vars":num_vars,
                        "connectivity":connectivity,
                        "num_leaves":num_leaves,
                        "num_found":num_found,
                        "num_no_diff":num_no_diff,
                        "num_other":num_other,
                        "target_recovery_rate":target_recovery_rate,
                        "min_depth":min_depth,
                        "max_depth":max_depth,
                        "avg_depth":avg_depth,
                        "min_num_exps":min_num_exps,
                        "max_num_exps":max_num_exps,
                        "avg_num_exps":avg_num_exps,
                    }
                )

    # Aggregated
    num_found = df['found'].sum() # Type 1: Found
    num_no_diff = df[df['msg'] == "NoDiff"].shape[0] # Type 2: No Difference
    num_other = df[df['msg'] == "Unknown"].shape[0] # Type 3: No Causal Link or Type 4: Noise Interference

    diff_df = df[df['msg'] != "NoDiff"]
    true_found_count = diff_df['found'].sum()
    total_rows = len(diff_df)
    target_recovery_rate = (true_found_count / total_rows)

    found_df = df[df['found']]
    # Depth information
    min_depth = found_df['depth'].min()
    max_depth = found_df['depth'].max()
    avg_depth = found_df['depth'].mean()

    # NumExps information
    min_num_exps = found_df['num_explanations'].min()
    max_num_exps = found_df['num_explanations'].max()
    avg_num_exps = found_df['num_explanations'].mean()

    table_data.append(
        {
            "num_vars":"All",
            "connectivity":"All",
            "num_leaves":"All",
            "num_found":num_found,
            "num_no_diff":num_no_diff,
            "num_other":num_other,
            "target_recovery_rate":target_recovery_rate,
            "min_depth":min_depth,
            "max_depth":max_depth,
            "avg_depth":avg_depth,
            "min_num_exps":min_num_exps,
            "max_num_exps":max_num_exps,
            "avg_num_exps":avg_num_exps,
        }
    )

    # Save table data
    csv_file = f'{COMPILED_DIR}results_random.csv'
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(table_data[0].keys()))
        writer.writeheader()
        writer.writerows(table_data)


if __name__ == "__main__":
    compile_cog_seq_results()
    compile_random_results()
