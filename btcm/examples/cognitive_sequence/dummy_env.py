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
    
    def reset_timer(self):
        # TODO: State changes
        return True

    def check_timer(self,_):
        pass

    def assess_user_sequence(self,_):
        pass

    def provide_sequence(self, state:CognitiveSequenceState):
        # TODO: State changes
        return True
    
    def reset_sequence_state(self,state:CognitiveSequenceState):
        # TODO: State changes
        return True
    
    def give_hint(self,state:CognitiveSequenceState):
        if state.vals["LatestUserAccuracy"] == "Perfect":
            return False
        return True
    
    def repeat_sequence_social_action(self, state:CognitiveSequenceState):
        if state.vals["LatestUserAccuracy"] == "Perfect":
            return False
        return True
    
    def end_sequence_social_action(self, _):
        return True
    
    def recapture_attention(self, _):
        # TODO: State changes
        return True
