from btcm.dm.state import State,VarRange
from btcm.dm.action import Action,NullAction


'''
STATE
'''
class CognitiveSequenceState(State):
    # Environmental Constants that cannot be intervened on
    MAX_NUM_REPETITIONS = 3 # Maximum number of times a particular sequence can be provided
    MAX_NUM_SEQUENCES = 3 # Maximum number of sequences that can be provided
    MAX_TIMEOUT = 4 # seconds

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
            "SequenceComplexity":VarRange.int_range(2,4), # The complexity of the sequence - the number of unique symbols used
            "SequenceLength":VarRange.int_range(4,8), # The length of the sequence - how many symbols used

            # External Game Variables
            "NumRepetitions":VarRange.int_range(0,self.MAX_NUM_REPETITIONS), # Number of times a particular sequence has been provided, to a maximum of MAX_NUM_SEQUENCES
            "NumSequences": VarRange.int_range(0,self.MAX_NUM_SEQUENCES), # Number of sequences that have been provided, to a maximum of MAX_NUM_SEQUENCES
            "SequenceSet": VarRange.boolean(), # boolean, if True a sequence has been set
            "ResponseTimerActive": VarRange.boolean(), # boolean, if True the response timer is active
            "UserResponded": VarRange.boolean(), # boolean, if True the user has responded with a sequence
            "AttemptedReengageUser":VarRange.boolean(), # Whether the robot attempted to reengage the user after a timeout

            # External User Variables
            "UserMemory":VarRange.normalised_float(), # The memory score of the user, between 0 and 1
            "UserAttention":VarRange.normalised_float(), # The attention score of the user, between 0 and 1
            "UserReactivity":VarRange.normalised_float(), # The reactivity score of the user, between 0 and 1
            "UserConfusion":VarRange.normalised_float(), # The confusion score of the user, between 0 and 1
            "UserEngagement":VarRange.normalised_float(), # The engagement score of the user, between 0 and 1
            "UserFrustration":VarRange.normalised_float(), # The frustration score of the user, between 0 and 1
            "UserAccuracy":VarRange.normalised_float(), # The observed accuracy of the user for a given sequence, between 0 and 1
            "UserResponseTime":VarRange.float_range(0,self.MAX_TIMEOUT), # The time taken for a user to respond to a given sequence, between 0 and MAX_TIMEOUT
        }
    
    def var_funcs(self) -> dict:
        return {
            key: (lambda key: lambda state: state.vals[key])(key)
            for key in self.ranges().keys()
        }
    
    def internal(self,var):
        internals = [
            "EndGame",
            "RepeatSequence",
            "SequenceComplexity",
            "SequenceLength"
        ]

        return var in internals
    
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
            "AttemptedReengageUser":False,

            # External User Variables
            "UserMemory":0.8,
            "UserAttention":0.8,
            "UserReactivity":0.8,
            "UserConfusion":0,
            "UserEngagement":0.8,
            "UserFrustration":0,
            "UserAccuracy":0,
            "UserResponseTime":0,
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
            "AttemptedReengageUser":"If true, the robot has attempted to reengage the user in the task.",

            # External User Variables
            "UserMemory":"A number from 0 to 1 representing the user's ability to recall sequences and instructions.",
            "UserAttention":"A number from 0 to 1 representing the user's attention span.",
            "UserReactivity":"A number from 0 to 1 representing the user's ability to respond quickly to sequences.",
            "UserConfusion":"A number from 0 to 1 representing the user's confusion about the current sequence, with 1 indicating complete confusion.",
            "UserEngagement":"A number from 0 to 1 representing the user's engagement in the task at the moment.",
            "UserFrustration":"A number from 0 to 1 representing the user's frustration with the current task.",
            "UserAccuracy":"A number from 0 to 1 representing the accuracy of the sequence a user has provided.",
            "UserResponseTime":f"The time it has taken for the user to respond to a sequence. If it equals the maximum value {CognitiveSequenceState.MAX_TIMEOUT}, then the user did not respond in time.",
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

    valid_lengths = ["Short","Medium","Long"]
    valid_complexities = ["Simple","Complex"]

    def __init__(self,sequence_length:str,sequence_complexity:str):
        super().__init__()

        if sequence_length not in self.valid_lengths:
            raise ValueError(f"Invalid sequence length: {sequence_length}. Must be one of {self.valid_lengths}.")
        self.sequence_length = sequence_length

        if sequence_complexity not in self.valid_complexities:
            raise ValueError(f"Invalid sequence complexity: {sequence_complexity}. Must be one of {self.valid_complexities}.")
        self.sequence_complexity = sequence_complexity

        self.name = f"{self.name}({self.sequence_length},{self.sequence_complexity})"

    @staticmethod
    def action_combos():
        return [
            SetSequenceParametersAction(length, complexity)
            for length in SetSequenceParametersAction.valid_lengths
            for complexity in SetSequenceParametersAction.valid_complexities
        ]
    
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



