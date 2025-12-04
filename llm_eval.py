import argparse
from os import walk
import csv
import ollama

from btcm.experiment import cognitive_sequence_experiment
from btcm.experiment import llm_explainer

LOG_DIR = "logs/cognitive_sequence/multi"

if __name__ == "__main__":
    '''
    Parse Arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p1', '--profile1', type=str)
    parser.add_argument('-p2', '--profile2', type=str)
    parser.add_argument('--hide_display', action='store_true')
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

    # Run
    for seed in seed_dict:
        file1 = seed_dict[seed][0]
        file2 = seed_dict[seed][1]

        if not args.hide_display:
            print(f"\n\n===Comparing {file1} and {file2}===")

        # TODO
        llm_explainer.llm_compare(
            file1=file1,
            file2=file2,
            target_profile=profile_name_2,
            log_dir1=log_dir1,
            log_dir2=log_dir2,
            hide_display=args.hide_display,
        )

        break 



