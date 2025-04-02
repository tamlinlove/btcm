from btcm.dm.state import State
from btcm.dm.action import Action,NullAction


'''
STATE
'''
class CognitiveSequenceState(State):
    MAX_NUM_SEQUENCES = 3

    def __init__(self, values = None):
        super().__init__(values)

    def ranges(self) -> dict:
        return {
            "EndGame": [True,False], # boolean, if True the game ends
            "NumSequences": list(range(self.MAX_NUM_SEQUENCES+1)), # Number of times a sequence has been provided, to a maximum of MAX_NUM_SEQUENCES
            "SequenceSet": [True,False], # boolean, if True a sequence has been set
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
            "EndGame":"Boolean variable indicating if the game must be ended",
            "NumSequences":f"Number of times a sequence has been provided, up to a maximum of {self.MAX_NUM_SEQUENCES}",
            "SequenceSet":"Boolean, if True a sequence has been set",
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



