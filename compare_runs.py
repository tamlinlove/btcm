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
    file1 = f"cog_log_{profile_name_1}.json"
    file2 = f"cog_log_{profile_name_2}.json"

    compare_runs(
        file1=file1,
        file2=file2,
        target_profile=profile_name_2,
        max_follow_ups=args.max_follow_ups,
        max_depth=args.max_depth,
        visualise=args.visualise,
        visualise_only_valid=args.visualise_only_valid,
        hide_display=args.hide_display,
    )