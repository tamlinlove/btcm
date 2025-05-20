import argparse
from os import walk

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

    founds = []
    depths = []
    for file1 in files1:
        for file2 in files2:
            if not args.hide_display:
                print(f"\n\n===Comparing {file1} and {file2}===")

            found,depth = compare_runs(
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

