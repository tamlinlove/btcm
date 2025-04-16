import argparse

from btcm.experiment import cognitive_sequence_experiment

from btcm.examples.cognitive_sequence.cognitive_sequence_environment import UserProfile
from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState

profile_experiments = {
    "default":cognitive_sequence_experiment.run_default,
    "perfect":cognitive_sequence_experiment.run_perfect,
    "worst":cognitive_sequence_experiment.run_worst,
    "no_attention":cognitive_sequence_experiment.run_no_attention,
    "no_reactivity":cognitive_sequence_experiment.run_no_reactivity,
}

if __name__ == "__main__":
    '''
    Parse Arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profile', type=str, required=True)
    parser.add_argument('-f', '--filename', type=str)
    args = parser.parse_args()

    '''
    Validation and Defaults
    '''
    # Profile
    profile_name = args.profile.lower()
    if profile_name not in profile_experiments:
        raise ValueError(f"Profile {args.profile} is not valid")
    
    # Filename
    filename = args.filename
    if args.filename is None:
        filename = f"cog_log_{profile_name}"

    '''
    Run Experiment
    '''
    profile_experiments[profile_name](filename=filename)

    