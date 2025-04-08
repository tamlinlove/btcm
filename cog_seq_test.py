import time
import py_trees

import btcm

from btcm.experiment import cognitive_sequence_experiment

from btcm.examples.cognitive_sequence.cognitive_sequence_environment import UserProfile
from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState

if __name__ == "__main__":
    # Default User Profile
    cognitive_sequence_experiment.run_default()

    # Distracted User Profile
    cognitive_sequence_experiment.run_distracted()

    