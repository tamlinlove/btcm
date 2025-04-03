import random

from btcm.dm.environment import Environment
from btcm.dm.action import NullAction

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState,SetSequenceParametersAction

'''
ENVIRONMENT
'''
class CognitiveSequenceEnvironment(Environment):
    def __init__(self,state:CognitiveSequenceState):
        super().__init__(state=state)

        # Internal State
        self.game_over = False
        self.number_of_sequences = 0
        self.sequence_length = None
        self.sequence_complexity = None
        self.sequence = ""


    '''
    ENVIRONMENT FUNCTIONS
    '''
    def generate_sequence(self):
        if self.sequence_length is None or self.sequence_complexity is None:
            raise ValueError("Sequence length and complexity must be set before generating a sequence.")
        
        # Generate a sequence based on the parameters
        if self.sequence_complexity == "Simple":
            characters = ["A", "B"]
        elif self.sequence_complexity == "Complex":
            characters = ["A", "B", "C", "D"]
        else:
            raise ValueError("Invalid complexity level. Choose 'Simple' or 'Complex'.")

        if self.sequence_length == "Short":
            seq_length = 3
        elif self.sequence_length == "Medium":
            seq_length = 6
        elif self.sequence_length == "Long":
            seq_length = 9
        else:
            raise ValueError("Invalid length. Choose 'Short', 'Medium', or 'Long'.")

        sequence = [random.choice(characters) for _ in range(seq_length)]
        return ''.join(sequence)

    '''
    ROBOT ACTIONS
    '''
    def end_game(self):
        self.game_over = True
        return True
    
    def set_sequence(self,set_params_action:SetSequenceParametersAction):
        if set_params_action == NullAction():
            return False

        # Set the parameters in the state
        self.sequence_length = set_params_action.sequence_length
        self.sequence_complexity = set_params_action.sequence_complexity
        self.sequence = self.generate_sequence()

        #print(f"SEQUENCE: {self.sequence}")

        return True