import argparse
import numpy as np

from btcm.experiment import cognitive_sequence_experiment

LOG_DIR = "logs/cognitive_sequence/multi"

if __name__ == "__main__":
    '''
    Parse Arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profiles', nargs='*', required=True)
    parser.add_argument('-n', '--num_exps', type=int, default=10)
    args = parser.parse_args()           

    '''
    Run Experiment
    '''
    seed = 0
    seed_interval = 1000
    for run in range(args.num_exps):
        print(f"Run {run+1}/{args.num_exps}")
        for profile in args.profiles:
            profile_name = profile.lower()
            if profile_name not in cognitive_sequence_experiment.profile_experiments:
                raise ValueError(f"Profile {profile} is not valid")
            
            filename = f"cog_log_{profile_name}_{seed}"

            # Set seed
            seed_override = (seed,seed+seed_interval)

            # Run
            cognitive_sequence_experiment.profile_experiments[profile_name](
                filename=filename,
                skip=True,
                display=False,
                log_dir=f"{LOG_DIR}/{profile_name}",
                seed_override=seed_override
            )

        seed += 1

    

    