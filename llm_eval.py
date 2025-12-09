import argparse
import os
from os import walk
import csv
import ollama

from btcm.experiment import cognitive_sequence_experiment
from btcm.experiment import llm_explainer

LOG_DIR = "logs/cognitive_sequence/multi"
DEFAULT_LLM_MODEL = "phi4"

if __name__ == "__main__":
    '''
    Parse Arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p1', '--profile1', type=str)
    parser.add_argument('-p2', '--profile2', type=str)
    parser.add_argument('-m', '--llm_model', type=str, default=DEFAULT_LLM_MODEL)
    parser.add_argument('--hide_display', action='store_true')
    parser.add_argument('--use_simple_prompt', action='store_true')
    args = parser.parse_args()

    '''
    Validation and Defaults
    '''
    # Profile
    profile_name_1 = args.profile1.lower()
    if profile_name_1 not in cognitive_sequence_experiment.profile_experiments:
        raise ValueError(f"Profile {args.profile1} is not valid")
    
    profile_name_2 = args.profile2.lower()
    if profile_name_2 not in cognitive_sequence_experiment.profile_experiments:
        raise ValueError(f"Profile {args.profile2} is not valid")
    
    # Filename
    log_dir1 = f"{LOG_DIR}/{profile_name_1}"
    log_dir2 = f"{LOG_DIR}/{profile_name_2}"
    files1 = next(walk(log_dir1), (None, None, []))[2]
    files2 = next(walk(log_dir2), (None, None, []))[2]

    # Matching files
    seed_dict = {}
    for file1 in files1:
        seed = file1.split("_")[-1].split(".")[0]
        seed_dict[seed] = [file1]

    for file2 in files2:
        seed = file2.split("_")[-1].split(".")[0]
        seed_dict[seed].append(file2)

    # Create save dir
    if args.use_simple_prompt:
        prompt_flag = "simple_"
    else:
        prompt_flag = ""
    save_path = f"results/{prompt_flag}{args.llm_model}"
    if not os.path.isdir(save_path):
        os.makedirs(save_path, exist_ok=True)

    # Run
    data = []
    for seed in seed_dict:
        file1 = seed_dict[seed][0]
        file2 = seed_dict[seed][1]

        if not args.hide_display:
            print(f"\n\n===Comparing {file1} and {file2}===")

        found,metrics,response,format_error = llm_explainer.llm_compare(
            file1=file1,
            file2=file2,
            target_profile=profile_name_2,
            log_dir1=log_dir1,
            log_dir2=log_dir2,
            model_name=args.llm_model,
            hide_display=args.hide_display,
            use_simple_prompt=args.use_simple_prompt
        )

        if not found:
            metrics = {
                "runtime":None,
                "num_exps":None,
                "target_recovered":None,
                "true_var_score":None,
                "true_val_score":None,
                "real_var_score":None,
            }


        data_row = metrics.copy()
        data_row["seed"] = seed
        data_row["found"] = found
        data_row["model"] = args.llm_model
        data_row["response"] = response
        data_row["format_error"] = format_error

    
        data.append(data_row)

    # Save
    
    csv_file = f'{save_path}/results_llm_{prompt_flag}{profile_name_1}_{profile_name_2}.csv'
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)



        



