from typing import Self

from btcm.dm.state import State,VarRange
from btcm.dm.action import Action,NullAction

'''
STATE
'''
class CognitiveSequenceState(State):
    # Environmental Constants that cannot be intervened on
    MAX_NUM_REPETITIONS = 3 # Maximum number of times a particular sequence can be provided
    MAX_NUM_SEQUENCES = 3 # Maximum number of sequences that can be provided
    MAX_TIMEOUT = 7 # seconds
    MIN_COMPLEXITY = 2
    MAX_COMPLEXITY = 4
    MIN_LENGTH = 4
    MAX_LENGTH = 8

    def __init__(self, values = None):
        super().__init__(values)

    '''
    VARIABLES
    '''

    def get_range_dict(self) -> dict:
        return {
            # Internal Game Variables
            "EndGame":VarRange.boolean(), # boolean, if True the game ends
            "RepeatSequence":VarRange.boolean(), # Whether the robot should repeat the current sequence or not
            "SequenceComplexity":VarRange.int_range(self.MIN_COMPLEXITY,self.MAX_COMPLEXITY), # The complexity of the sequence - the number of unique symbols used
            "SequenceLength":VarRange.int_range(self.MIN_LENGTH,self.MAX_LENGTH), # The length of the sequence - how many symbols used
            "NumRepetitions":VarRange.int_range(0,self.MAX_NUM_REPETITIONS), # Number of times a particular sequence has been provided, to a maximum of MAX_NUM_SEQUENCES
            "NumSequences": VarRange.int_range(0,self.MAX_NUM_SEQUENCES), # Number of sequences that have been provided, to a maximum of MAX_NUM_SEQUENCES
            "SequenceSet": VarRange.boolean(), # boolean, if True a sequence has been set

            # External Game Variables
            "ResponseTimerActive": VarRange.boolean(), # boolean, if True the response timer is active
            "UserResponded": VarRange.boolean(), # boolean, if True the user has responded with a sequence
            "UserTimeout": VarRange.boolean(), # boolean, if True the timeout expired before the user could respond
            "AttemptedReengageUser":VarRange.boolean(), # Whether the robot attempted to reengage the user after a timeout

            # Non-intervenable Game Variables
            "CurrentSequence": VarRange.any_string(), # The current sequence provided to the user
            "UserSequence": VarRange.any_string(), # The current sequence responded by the user
            "AccuracySeed": VarRange.any_int(), # The seed used to generate random errors by the user, saved for reproducibility
            "ResponseTimeSeed": VarRange.any_int(), # The seed used to generate random response times by the user, saved for reproducibility

            # External User Variables
            "UserMemory":VarRange.normalised_float(), # The memory score of the user, between 0 and 1
            "UserAttention":VarRange.normalised_float(), # The attention score of the user, between 0 and 1
            "UserReactivity":VarRange.normalised_float(), # The reactivity score of the user, between 0 and 1
            "UserConfusion":VarRange.normalised_float(), # The confusion score of the user, between 0 and 1
            "UserEngagement":VarRange.normalised_float(), # The engagement score of the user, between 0 and 1
            "UserFrustration":VarRange.normalised_float(), # The frustration score of the user, between 0 and 1
            "BaseUserAccuracy":VarRange.normalised_float(), # The base accuracy of the user for a given sequence, between 0 and 1
            "BaseUserResponseTime":VarRange.float_range(0,self.MAX_TIMEOUT), # The base time taken for a user to respond to a given sequence, between 0 and MAX_TIMEOUT
            "ObservedUserResponseTime":VarRange.float_range(0,self.MAX_TIMEOUT), # The observed time taken for a user to respond to a given sequence, between 0 and MAX_TIMEOUT
        }
    
    def internal(self,var):
        internals = [
            "EndGame",
            "RepeatSequence",
            "SequenceComplexity",
            "SequenceLength",
            "NumRepetitions",
            "NumSequences",
            "SequenceSet",
            # Non-intervenable
            "CurrentSequence",
            "AccuracySeed",
            "ResponseTimeSeed",
        ]

        return var in internals
    
    '''
    VARIABLE FUNCTIONS
    '''
    def var_funcs(self) -> dict:
        # Most variables don't have a special function...
        func_dict = {
            key: (lambda key: lambda state: state.vals[key])(key)
            for key in self.ranges().keys()
        }

        # ...but some do:
        func_dict["UserConfusion"] = self.get_confusion
        func_dict["UserEngagement"] = self.get_engagement
        func_dict["UserAccuracy"] = self.get_accuracy
        func_dict["UserResponseTime"] = self.get_time

        return func_dict
    
    @staticmethod
    def get_confusion(state:Self,memory_weight=0.5,complexity_weight=0.5) -> float:
        normalised_complexity = 0.5*state["SequenceComplexity"] - 1
        confusion = memory_weight * (1 - state["UserMemory"]) + complexity_weight * normalised_complexity
        return max(0, min(1, confusion))
    
    @staticmethod
    def get_engagement(state:Self,confusion_weight=0.5,attention_weight=0.5) -> float:
        engagement = confusion_weight * (1 - state["UserConfusion"]) + attention_weight * state["UserAttention"]
        return max(0, min(1, engagement))
    
    @staticmethod
    def get_accuracy(state:Self) -> float:
        if state["SequenceComplexity"] == 2:
            # Very simple
            accuracy = -0.75 * state["UserConfusion"] + 0.95
        elif state["SequenceComplexity"] == 3:
            # Medium
            accuracy = -0.8 * state["UserConfusion"] + 0.9
        elif state["SequenceComplexity"] == 4:
            # Complex
            accuracy = -0.85 * state["UserConfusion"] + 0.85

        return max(0, min(1, accuracy))
    
    @staticmethod
    def get_time(state:Self,reactivity_weight=0.4,confusion_weight=0.3,engagement_weight=0.3) -> float:
        time_factor = reactivity_weight*state["UserReactivity"] + confusion_weight*(1-state["UserConfusion"]) + engagement_weight*state["UserEngagement"]
        time_factor = max(0, min(1, time_factor))

        base_time_gradient = 0.625 * state["SequenceLength"]
        base_min_time = 0.5 * state["SequenceLength"]

        base_time_taken = base_time_gradient * (1 - time_factor) + base_min_time

        return base_time_taken
    
    '''
    EXECUTION
    '''

    def run(self,node:str,state:State):
        return self.var_funcs()[node](state)
    
    '''
    ACTIONS
    '''
    
    def retrieve_action(self, action_name):
        if action_name == "NullAction":
            return NullAction()
        elif action_name == "EndGame":
            return EndGameAction()
        elif action_name == "ProvideSequence":
            return ProvideSequenceAction()
        elif action_name == "CrashAction":
            return CrashAction()
        elif action_name.startswith("SetSequenceParameters"):
            return SetSequenceParametersAction(
                action_name.split("(")[1].split(",")[0],
                action_name.split(",")[1].split(")")[0]
            )
        elif action_name == "ResetTimer":
            return ResetTimerAction()
        elif action_name == "CheckTimer":
            return CheckTimerAction()
        elif action_name == "AssessSequence":
            return AssessSequenceAction()
        elif action_name == "EndThisSequence":
            return EndThisSequenceAction()
        elif action_name == "RepeatThisSequence":
            return RepeatThisSequenceAction()
        elif action_name == "RecaptureAttention":
            return RecaptureAttentionAction()
        elif action_name == "EndSequenceSocial":
            return EndSequenceSocialAction()
        elif action_name == "RepeatSequenceSocial":
            return RepeatSequenceSocialAction()
        elif action_name == "GiveSequenceHint":
            return GiveSequenceHintAction()
        else:
            raise ValueError(f"Unknown action name: {action_name}")
        
    '''
    VALUES
    '''
        
    @staticmethod
    def default_values():
        return {
            # Internal Game Variables
            "EndGame":False,
            "RepeatSequence":False,
            "SequenceComplexity":3,
            "SequenceLength":4,

            # External Game Variables
            "NumRepetitions":0,
            "NumSequences": 0,
            "SequenceSet": False,
            "ResponseTimerActive": False,
            "UserResponded": False,
            "UserTimeout": False,
            "AttemptedReengageUser":False,

            # Non-intervenable Game Variables
            "CurrentSequence": "",
            "UserSequence": "",
            "AccuracySeed": 0,
            "ResponseTimeSeed": 0,

            # External User Variables
            "UserMemory":0.8,
            "UserAttention":0.8,
            "UserReactivity":0.8,
            "UserConfusion":0,
            "UserEngagement":0.8,
            "UserFrustration":0,
            "BaseUserAccuracy":0,
            "BaseUserResponseTime":0,
            "ObservedUserResponseTime":0,
        }

    '''
    CAUSAL MODEL
    '''
    def cm_edges(self) -> list[tuple[str,str]]:
        return []
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_dict(self) -> dict[str,str]:
        return {
            # Internal Game Variables
            "EndGame":"Represents the decision to end the game at the next available moment.",
            "RepeatSequence":"Represents the decision to repeat the current sequence rather than end the game or move to a new sequence.",
            "SequenceComplexity":"The complexity of the sequence - determined by the number of unique symbols used.",
            "SequenceLength":"The length of the sequence - determined by the number of characters in the sequence.",

            # External Game Variables
            "NumRepetitions":"The number of times the current sequence has been repeated.",
            "NumSequences": "The number of unique sequences that have been provided thus far.",
            "SequenceSet": "If true, the sequence has been decided upon this round. False otherwise.",
            "ResponseTimerActive": "If true, the robot has activated a timer and is waiting for the user to repeat a sequence.",
            "UserResponded": "If true, the user has repeated (successfully or not) the sequence back to the robot.",
            "UserTimeout": "If true the timeout expired before the user could respond.",
            "AttemptedReengageUser":"If true, the robot has attempted to reengage the user in the task.",

            # Non-intervenable Game Variables
            "CurrentSequence": "A string of characters representing the current sequence provided to the user.",
            "UserSequence": "A string of characters representing the current sequence responded by the user.",
            "AccuracySeed": "The seed used to generate random errors by the user, saved for reproducibility.",
            "ResponseTimeSeed": "The seed used to generate random response times by the user, saved for reproducibility.",

            # External User Variables
            "UserMemory":"A number from 0 to 1 representing the user's ability to recall sequences and instructions.",
            "UserAttention":"A number from 0 to 1 representing the user's attention span.",
            "UserReactivity":"A number from 0 to 1 representing the user's ability to respond quickly to sequences.",
            "UserConfusion":"A number from 0 to 1 representing the user's confusion about the current sequence, with 1 indicating complete confusion.",
            "UserEngagement":"A number from 0 to 1 representing the user's engagement in the task at the moment.",
            "UserFrustration":"A number from 0 to 1 representing the user's frustration with the current task.",
            "BaseUserAccuracy":"A number from 0 to 1 representing the base accuracy of the sequence a user has provided.",
            "BaseUserResponseTime":f"The base time it takes for the user to respond to a sequence. If it equals the maximum value {CognitiveSequenceState.MAX_TIMEOUT}, then the user did not respond in time.",
            "ObservedUserResponseTime":f"The observed time it has taken for the user to respond to a sequence. If it equals the maximum value {CognitiveSequenceState.MAX_TIMEOUT}, then the user did not respond in time.",
        }


'''
ACTIONS
'''
class EndGameAction(Action):
    name = "EndGame"

    def __init__(self):
        super().__init__()

class SetSequenceParametersAction(Action):
    name = "SetSequenceParameters"

    def __init__(self,sequence_length:int,sequence_complexity:int):
        super().__init__()

        if sequence_length < CognitiveSequenceState.MIN_LENGTH or sequence_length > CognitiveSequenceState.MAX_LENGTH:
            raise ValueError(f"Cannot set a sequence of length {sequence_length}, must be between {CognitiveSequenceState.MIN_LENGTH} and {CognitiveSequenceState.MAX_LENGTH}")
        self.sequence_length = sequence_length

        if sequence_complexity < CognitiveSequenceState.MIN_COMPLEXITY or sequence_complexity > CognitiveSequenceState.MAX_COMPLEXITY:
            raise ValueError(f"Cannot set a sequence of complexity {sequence_complexity}, must be between {CognitiveSequenceState.MIN_COMPLEXITY} and {CognitiveSequenceState.MAX_COMPLEXITY}")
        self.sequence_complexity = sequence_complexity

        self.name = f"{self.name}({self.sequence_length},{self.sequence_complexity})"

    @staticmethod
    def action_combos():
        combos = []

        for length in range(CognitiveSequenceState.MIN_LENGTH, CognitiveSequenceState.MAX_LENGTH + 1):
            for complexity in range(CognitiveSequenceState.MIN_COMPLEXITY, CognitiveSequenceState.MAX_COMPLEXITY + 1):
                combos.append(SetSequenceParametersAction(length,complexity))

        return combos
    
class ProvideSequenceAction(Action):
    name = "ProvideSequence"

    def __init__(self):
        super().__init__()

class CrashAction(Action):
    name = "CrashAction"

    def __init__(self):
        super().__init__()

class ResetTimerAction(Action):
    name = "ResetTimer"

    def __init__(self):
        super().__init__()

class CheckTimerAction(Action):
    name = "CheckTimer"

    def __init__(self):
        super().__init__()

class AssessSequenceAction(Action):
    name = "AssessSequence"

    def __init__(self):
        super().__init__()

class EndThisSequenceAction(Action):
    name = "EndThisSequence"

    def __init__(self):
        super().__init__()

class RepeatThisSequenceAction(Action):
    name = "RepeatThisSequence"

    def __init__(self):
        super().__init__()

class RecaptureAttentionAction(Action):
    name = "RecaptureAttention"

    def __init__(self):
        super().__init__()

class EndSequenceSocialAction(Action):
    name = "EndSequenceSocial"

    def __init__(self):
        super().__init__()

class RepeatSequenceSocialAction(Action):
    name = "RepeatSequenceSocial"

    def __init__(self):
        super().__init__()

class GiveSequenceHintAction(Action):
    name = "GiveSequenceHint"

    def __init__(self):
        super().__init__()



