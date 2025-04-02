import py_trees

from btcm.bt.nodes import ActionNode,ConditionNode
from btcm.dm.action import Action,NullAction

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState, SetSequenceParametersAction,ProvideSequenceAction, CrashAction

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
    
class SetSequenceParameters(ActionNode):
    def __init__(self, name:str = "SetSequenceParameters"):
        super(SetSequenceParameters, self).__init__(name)

        # Requires write access to environment and state
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)
        self.board.register_key("state", access=py_trees.common.Access.WRITE)

    def decide(self, state:CognitiveSequenceState):
        # TODO: Logic for setting sequence parameters
        return NullAction()

    def execute(self, state:CognitiveSequenceState, action:Action):
        # Ask environment for a sequence based on parameters
        status = self.board.environment.set_sequence(action)

        if status:
            # Update the state with the new sequence
            state.vals["SequenceSet"] = True
            return py_trees.common.Status.SUCCESS
        
        # If the action was not successful, return failure
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return []
    
    def action_space(self):
        all_combos = SetSequenceParametersAction.action_combos()
        return all_combos + [NullAction()]
    
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
    
class ProvideSequence(ActionNode):
    def __init__(self, name:str = "ProvideSequence"):
        super(ProvideSequence, self).__init__(name)

        # Requires write access to environment
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def decide(self, _):
        # Always presents the sequence that was selected
        return ProvideSequenceAction()
    
    def execute(self, _, action):
        # TODO: logic for presenting the sequence
        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return []
    
    def action_space(self):
        return [ProvideSequenceAction(),NullAction()]
    
'''
COMPOSITE NODES
'''
def start_game_subtree():
    check_initial_and_set_params_sequence = py_trees.composites.Sequence(
        name = "CheckInitialAndSetParamsSequence",
        memory = False,
        children = [
            CheckInitialSequence(),
            SetSequenceParameters()
        ]
    )

    set_params_or_handle_repeated_fallback = py_trees.composites.Selector(
        name = "SetParamsOrHandleRepeatedFallback",
        memory = False,
        children = [
            check_initial_and_set_params_sequence,
            HandleRepeatedSequence()
        ]
    )

    start_game_sequence = py_trees.composites.Sequence(
        name = "StartGameSequence",
        memory = False,
        children = [
            set_params_or_handle_repeated_fallback,
            ProvideSequence()
        ]
    )

    return start_game_sequence