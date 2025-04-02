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
        # TODO: write logic to generate a sequence
        if self.sequence_length is None or self.sequence_complexity is None:
            raise ValueError("Sequence length and complexity must be set before generating a sequence.")
        
        # Generate a sequence based on the parameters
        sequence = "AABB"

        return sequence

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

        return True