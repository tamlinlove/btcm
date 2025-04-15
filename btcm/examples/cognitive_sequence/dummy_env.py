from btcm.dm.action import NullAction

from btcm.examples.cognitive_sequence.cognitive_sequence_environment import CognitiveSequenceEnvironment, UserProfile
from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState,SetSequenceParametersAction

class DummyCognitiveSequenceEnvironment(CognitiveSequenceEnvironment):
    '''
    Mocks the real CognitiveSequenceEnvironment class, but doesn't enact any changes on the input states, to allow for sensible interventions
    '''
    def __init__(self):
        # TODO: Use causal model structure to avoid overriding intervened variables? Or maybe not?
        pass

    '''
    ROBOT ACTIONS
    '''
    def end_game(self):
        return True
    
    def provide_sequence(self, state:CognitiveSequenceState):
        # TODO: State changes
        return True
    
    def reset_timer(self):
        return True

    def check_timer(self,_):
        # TODO: State changes
        pass
    
    def reset_sequence_state(self,state:CognitiveSequenceState):
        # TODO: State changes
        return True
    
    def give_hint(self,state:CognitiveSequenceState):
        pass
    
    def repeat_sequence_social_action(self, state:CognitiveSequenceState):
        pass
    
    def end_sequence_social_action(self, _):
        pass
    
    def recapture_attention(self, _):
        pass
