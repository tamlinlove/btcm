from btcm.dm.state import State
from btcm.dm.action import Action,NullAction


'''
STATE
'''
class CognitiveSequenceState(State):
    MAX_NUM_SEQUENCES = 3
    MAX_TIMEOUT = 10 # seconds

    def __init__(self, values = None):
        super().__init__(values)

    def ranges(self) -> dict:
        return {
            # Game state variables
            "EndGame": [True,False], # boolean, if True the game ends
            "NumSequences": list(range(self.MAX_NUM_SEQUENCES+1)), # Number of times a sequence has been provided, to a maximum of MAX_NUM_SEQUENCES
            "SequenceSet": [True,False], # boolean, if True a sequence has been set
            "ResponseTimerActive": [True,False], # boolean, if True the response timer is active
            "UserResponded": [True,False], # boolean, if True the user has responded with a sequence
            "UserResponseTime": list(range(self.MAX_TIMEOUT+1)), # User response time in seconds, to a maximum of MAX_TIMEOUT
            "LatestUserAccuracy":["Perfect","Good","Medium","Poor","CompletelyWrong"], # User accuracy in the last sequence attempt
            "LatestUserSpeed":["Faster","Normal","Slower"], # User speed in the last sequence attempt, taking into account sequence difficulty
            "AttemptedReengageUser":[True,False], # Whether the robot attempted to reengage the user after a timeout
            "RepeatSequence":[True,False], # Whether the robot should repeat the current sequence or not

            # User progress variables
            "UserAccuracy":["High","Medium","Low"], # User accuracy level
            "UserSpeed":["Fast","Medium","Slow"], # User speed level

            # User state variables
            "UserStruggling":[True,False,None], # User struggling with the task
            "UserAttention":["High","Medium","Low"], # User attention level
            "UserFrustration":["High","Medium","Low"], # User frustration level
            "UserConfusion":["High","Medium","Low"], # User confusion level
        }
    
    def var_funcs(self) -> dict:
        return {
            key: (lambda key: lambda state: state.vals[key])(key)
            for key in self.ranges().keys()
        }
    
    def run(self,node:str,state:State):
        return self.var_funcs()[node](state)
    
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
        else:
            raise ValueError(f"Unknown action name: {action_name}")

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
            # Game state variables
            "EndGame":"Boolean variable indicating if the game must be ended",
            "NumSequences":f"Number of times a sequence has been provided, up to a maximum of {self.MAX_NUM_SEQUENCES}",
            "SequenceSet":"Boolean, if True a sequence has been set",
            "ResponseTimerActive":"Boolean, if True the robot is waiting for the user to respond",
            "UserResponded":"Boolean, if True the user has responded with a sequence",
            "UserResponseTime":"The time taken by the user to respond, in seconds",
            "LatestUserAccuracy":"A measure of how well the user did in their last sequence attempt",
            "LatestUserSpeed":"A measure of how fast the user was in their last sequence attempt, taking into account sequence difficulty",
            "AttemptedReengageUser":"Boolean, if True the robot attempted to reengage the user after a timeout",
            "RepeatSequence":"Boolean, if True the robot should repeat the current sequence",

            # User progress variables
            "UserAccuracy":"The user's accuracy thusfar",
            "UserSpeed":"The speed of the user in repeating the sequence",

            # User state variables
            "UserStruggling":"Whether or not the user is struggling to repeat the sequence. If None, value is unknown",
            "UserAttention":"The level of attention the user is paying to the task",
            "UserFrustration":"The level of frustration the user is experiencing",
            "UserConfusion":"The level of confusion the user is experiencing",
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



