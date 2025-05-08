import argparse

from btcm.experiment import cognitive_sequence_experiment
from btcm.experiment.cognitive_sequence_explainer import explain_single

if __name__ == "__main__":
    '''
    Parse Arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profile', type=str)
    parser.add_argument('-f', '--filename', type=str)
    parser.add_argument('-n', '--nodename', type=str, default="SequenceLength")
    parser.add_argument('-t', '--nodetype', type=str, default="State")
    parser.add_argument('-i', '--tick', type=int, default=0)
    parser.add_argument('-j', '--time', default="end")
    parser.add_argument('-v', '--foils', type=int, nargs='*', default=None)
    parser.add_argument('--hide_display', action='store_true')
    parser.add_argument('--visualise',  action='store_true')
    parser.add_argument('--visualise_only_valid',  action='store_true')
    parser.add_argument('--max_depth',  type=int, default=1)
    args = parser.parse_args()

    '''
    Validation and Defaults
    '''
    if args.profile is None and args.filename is None:
        raise ValueError("Please provide a profile or filename")

    # Profile
    profile_name = args.profile.lower()
    if profile_name not in cognitive_sequence_experiment.profile_experiments:
        raise ValueError(f"Profile {args.profile} is not valid")
    
    # Filename
    filename = args.filename
    if args.filename is None:
        filename = f"cog_log_{profile_name}"
    file = f"{filename}.json"

    explain_single(
        file=file,
        nodename=args.nodename,
        nodetype=args.nodetype,
        tick=args.tick,
        time=args.time,
        foils=args.foils,
        max_depth=args.max_depth,
        visualise=args.visualise,
        visualise_only_valid=args.visualise_only_valid,
        hide_display=args.hide_display,
    )