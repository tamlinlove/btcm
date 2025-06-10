import argparse
from os import walk
import csv

from btcm.experiment import cognitive_sequence_experiment
from btcm.experiment.cognitive_sequence_explainer import compare_runs

LOG_DIR = "logs/cognitive_sequence/multi"

if __name__ == "__main__":
    '''
    Parse Arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p1', '--profile1', type=str)
    parser.add_argument('-p2', '--profile2', type=str)
    parser.add_argument('--hide_display', action='store_true')
    parser.add_argument('--visualise',  action='store_true')
    parser.add_argument('--visualise_only_valid',  action='store_true')
    parser.add_argument('--max_depth',  type=int, default=1)
    parser.add_argument('--max_follow_ups',  type=int, default=2)
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

    # RUN
    founds = []
    depths = []
    nums_exps = []
    data = []
    msgs = []
    for seed in seed_dict:
        file1 = seed_dict[seed][0]
        file2 = seed_dict[seed][1]

        if not args.hide_display:
            print(f"\n\n===Comparing {file1} and {file2}===")

        found,depth,num_exps,msg = compare_runs(
            file1=file1,
            file2=file2,
            target_profile=profile_name_2,
            log_dir1=log_dir1,
            log_dir2=log_dir2,
            max_follow_ups=args.max_follow_ups,
            max_depth=args.max_depth,
            visualise=args.visualise,
            visualise_only_valid=args.visualise_only_valid,
            hide_display=args.hide_display,
        )

        founds.append(found)
        depths.append(depth)
        nums_exps.append(num_exps)  
        msgs.append(msg)

        data.append(
            {
                'seed': seed,
                'found': found,
                'depth': depth,
                'num_explanations': num_exps,
                'msg': msg
            }
        )

    percentage = (sum(founds) / len(founds)) * 100
    print(f"{percentage}% of comparisons successfully recovered target variable")

    unique_vals = sorted(list(set(depths)))
    for u in unique_vals:
        new_list = [d==u for d in depths]
        percentage = (sum(new_list) / len(new_list)) * 100
        if u == 0:
            print(f"{percentage}% of comparisons did not recover the target variable")
        elif u == 1:
            print(f"{percentage}% of comparisons recovered the target variable in 1 step")
        else:
            print(f"{percentage}% of comparisons recovered the target variable in {u} steps")

    # Save
    csv_file = f'results/results_{profile_name_1}_{profile_name_2}.csv'
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['seed', 'found', 'depth', 'num_explanations', 'msg'])
        writer.writeheader()
        writer.writerows(data)

