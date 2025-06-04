import argparse

from btcm.experiment import cognitive_sequence_experiment
from btcm.experiment.cognitive_sequence_explainer import compare_runs

if __name__ == "__main__":
    '''
    Parse Arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p1', '--profile1', type=str)
    parser.add_argument('-p2', '--profile2', type=str)
    parser.add_argument('-f1', '--file1', type=str)
    parser.add_argument('-f2', '--file2', type=str)
    parser.add_argument('--hide_display', action='store_true')
    parser.add_argument('--visualise',  action='store_true')
    parser.add_argument('--visualise_only_valid',  action='store_true')
    parser.add_argument('--max_depth',  type=int, default=1)
    parser.add_argument('--max_follow_ups',  type=int, default=2)
    parser.add_argument('--multi',  action='store_true')
    parser.add_argument('--seed',  type=int)
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
    

    if args.multi:
        if args.seed is None:
            raise ValueError("Seed must be provided for multi-profile comparison")
        log_dir = "logs/cognitive_sequence/multi/"
        log_dir1 = f"{log_dir}{profile_name_1}/"
        log_dir2 = f"{log_dir}{profile_name_2}/"
        file1 = f"cog_log_{profile_name_1}_{args.seed}.json"
        file2 = f"cog_log_{profile_name_2}_{args.seed}.json"

    else:
        # Filename
        if args.file1 is None:
            file1 = f"cog_log_{profile_name_1}.json"
        else:
            file1 = args.file1
        if args.file2 is None:
            file2 = f"cog_log_{profile_name_2}.json"
        else:
            file2 = args.file2
        log_dir1 = cognitive_sequence_experiment.LOG_DIRECTORY
        log_dir2 = cognitive_sequence_experiment.LOG_DIRECTORY

    compare_runs(
        file1=file1,
        file2=file2,
        log_dir1=log_dir1,
        log_dir2=log_dir2,
        target_profile=profile_name_2,
        max_follow_ups=args.max_follow_ups,
        max_depth=args.max_depth,
        visualise=args.visualise,
        visualise_only_valid=args.visualise_only_valid,
        hide_display=args.hide_display,
    )