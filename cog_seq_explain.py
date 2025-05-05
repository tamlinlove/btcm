import argparse

from btcm.experiment import cognitive_sequence_experiment
from btcm.experiment.cognitive_sequence_explainer import explain_single

if __name__ == "__main__":
    '''
    Parse Arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profile', type=str, required=True)
    parser.add_argument('-f', '--filename', type=str)
    parser.add_argument('--visualise',  action='store_true')
    args = parser.parse_args()

    '''
    Validation and Defaults
    '''
    # Profile
    profile_name = args.profile.lower()
    if profile_name not in cognitive_sequence_experiment.profile_experiments:
        raise ValueError(f"Profile {args.profile} is not valid")
    
    # Filename
    filename = args.filename
    if args.filename is None:
        filename = f"cog_log_{profile_name}"
    
    '''
    Load file and BT
    '''

    file = f"{filename}.json"

    nodename = "SequenceLength"
    nodetype = "State"
    tick = 0
    time = 4
    foils = None #[6]

    '''
    nodename = "SetSequenceParameters"
    nodetype = "Decision"
    tick = 0
    time = 4
    foils = None
    '''

    '''
    nodename = "DecideSocialAction"
    nodetype = "Decision"
    tick = 1
    time = 27
    foils = None
    '''

    explain_single(
        profile_name=profile_name,
        file=file,
        nodename=nodename,
        nodetype=nodetype,
        tick=tick,
        time=time,
        max_depth=1,
        visualise=args.visualise
    )