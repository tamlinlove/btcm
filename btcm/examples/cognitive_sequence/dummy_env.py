from btcm.dm.action import NullAction

from btcm.examples.cognitive_sequence.cognitive_sequence_environment import CognitiveSequenceEnvironment, UserProfile
from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState,SetSequenceParametersAction

class DummyCognitiveSequenceEnvironment(CognitiveSequenceEnvironment):
    '''
    Mocks the real CognitiveSequenceEnvironment class, but doesn't enact any changes on the input states, to allow for sensible interventions
    '''
    def __init__(self):
        pass

    '''
    ROBOT ACTIONS
    '''
    def end_game(self):
        return True
    
    def set_sequence(self,set_params_action:SetSequenceParametersAction):
        if set_params_action == NullAction():
            return False
        return True
    
    def reset_timer(self):
        return True

    def check_timer(self,_):
        pass

    def assess_user_sequence(self,_):
        pass

    def provide_sequence(self, state:CognitiveSequenceState):
        if not state.vals["SequenceSet"]:
            return False
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
        return True
