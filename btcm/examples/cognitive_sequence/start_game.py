import py_trees

from btcm.bt.nodes import ActionNode,ConditionNode
from btcm.dm.action import Action,NullAction

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState, SetSequenceParametersAction,ProvideSequenceAction, CrashAction
from btcm.examples.cognitive_sequence.handle_user_response import handle_user_response_subtree

'''
LEAF NODES
'''
class CheckInitialSequence(ConditionNode):
    def __init__(self, name:str = "CheckInitialSequence"):
        super(CheckInitialSequence, self).__init__(name)

    def execute(self, state, _):
        if state.vals["NumSequences"] == 0:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return ["NumSequences"]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_description(self) -> str:
        return "Checks if a sequence has already been set or not. If not, it returns SUCCESS, otherwise FAILURE."
    
class SetSequenceParameters(ActionNode):
    def __init__(self, name:str = "SetSequenceParameters"):
        super(SetSequenceParameters, self).__init__(name)

        # Requires write access to environment and state
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)
        self.board.register_key("state", access=py_trees.common.Access.WRITE)

    def decide(self, state:CognitiveSequenceState):
        # Initialise difficulty parameters
        length = "Medium"
        complexity = "Simple"

        # Adjust length based on user's speed and accuracy
        if state.vals["UserSpeed"] == "Fast" and state.vals["UserAccuracy"] == "High":
            length = "Long"
        elif state.vals["UserSpeed"] == "Slow" or state.vals["UserAccuracy"] == "Low":
            length = "Short"

        # Adjust complexity based on user's attention, frustration, and confusion
        if state.vals["UserAttention"] == "High" and state.vals["UserFrustration"] == "Low" and state.vals["UserConfusion"] == "Low":
            complexity = "Complex"
        elif state.vals["UserAttention"] == "Low" or state.vals["UserFrustration"] == "High" or state.vals["UserConfusion"] == "High":
            complexity = "Simple"

        return SetSequenceParametersAction(length, complexity)

    def execute(self, state:CognitiveSequenceState, action:Action):
        # Ask environment for a sequence based on parameters
        status = self.board.environment.set_sequence(action)

        if status:
            # Update the state with the new sequence
            #self.board.state.vals["SequenceSet"] = True
            state.vals["SequenceSet"] = True
            return py_trees.common.Status.SUCCESS
        
        # If the action was not successful, return failure
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return ["UserSpeed","UserAccuracy","UserAttention","UserFrustration","UserConfusion"]
    
    def action_space(self):
        all_combos = SetSequenceParametersAction.action_combos()
        return all_combos + [NullAction()]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_description(self) -> str:
        return "Sets the parameters for the sequence, based on a number of human factors in the state."
    
class HandleRepeatedSequence(ActionNode):
    def __init__(self, name:str = "HandleRepeatedSequence"):
        super(HandleRepeatedSequence, self).__init__(name)

    def decide(self, state:CognitiveSequenceState):
        # TODO: Implement something proper
        if state.vals["SequenceSet"]:
            return NullAction()
        return CrashAction()
    
    def execute(self, _, action:Action):
        if action == CrashAction():
            return py_trees.common.Status.FAILURE
        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["SequenceSet"]
    
    def action_space(self):
        return [CrashAction(),NullAction()]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_description(self) -> str:
        return "Handles the case where a sequence has already been set."
    
class ProvideSequence(ActionNode):
    def __init__(self, name:str = "ProvideSequence"):
        super(ProvideSequence, self).__init__(name)

        # Requires write access to state and environment
        self.board.register_key("state", access=py_trees.common.Access.WRITE)
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def decide(self, _):
        # Always presents the sequence that was selected
        return ProvideSequenceAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        # Present the sequence to the user
        status = self.board.environment.provide_sequence()
        if not status:
            return py_trees.common.Status.FAILURE

        # Update number of sequences
        #self.board.state.vals["NumSequences"] += 1
        state.vals["NumSequences"] += 1
        state.vals["UserResponded"] = False

        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return []
    
    def action_space(self):
        return [ProvideSequenceAction(),NullAction()]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_description(self) -> str:
        return "Presents the sequence that was selected."
    
'''
COMPOSITE NODES
'''

def start_game_subtree():
    check_initial_and_set_params_sequence = py_trees.composites.Sequence(
        name = "CheckInitialAndSetParamsSequence",
        memory = True,
        children = [
            CheckInitialSequence(),
            SetSequenceParameters()
        ]
    )

    set_params_or_handle_repeated_fallback = py_trees.composites.Selector(
        name = "SetParamsOrHandleRepeatedFallback",
        memory = True,
        children = [
            check_initial_and_set_params_sequence,
            HandleRepeatedSequence()
        ]
    )

    start_game_sequence = py_trees.composites.Sequence(
        name = "StartGameSequence",
        memory = True,
        children = [
            set_params_or_handle_repeated_fallback,
            ProvideSequence(),
            handle_user_response_subtree()
        ]
    )

    return start_game_sequence