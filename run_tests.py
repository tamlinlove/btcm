import argparse

from btcm.experiment import cognitive_sequence_experiment

if __name__ == "__main__":
    '''
    Parse Arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', action='store_true')
    parser.add_argument('--display', action='store_true')
    args = parser.parse_args()

    '''
    Run Experiment
    '''
    for profile_name in cognitive_sequence_experiment.profile_experiments:
        filename = f"cog_log_{profile_name}"
        cognitive_sequence_experiment.profile_experiments[profile_name](filename=filename,skip=args.skip,display=args.display)
        if args.display:
            print("\n\n\n")