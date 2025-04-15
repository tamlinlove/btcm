import py_trees
import numpy as np

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
        if state.vals["NumRepetitions"] == 0:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return ["NumRepetitions"]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_description(self) -> str:
        return "Checks if a sequence has already been set or not. If not, it returns SUCCESS, otherwise FAILURE."
    
class SetSequenceParameters(ActionNode):
    def __init__(self, name:str = "SetSequenceParameters"):
        super(SetSequenceParameters, self).__init__(name)

    def decide(self, state:CognitiveSequenceState):
        # Initialise difficulty parameters

        if state.vals["NumSequences"] == 0:
            # This is the very first parameter setting, cannot use previous sequences
            
            # First, decide on complexity using memory and attention
            complexity_score = state.vals["UserMemory"] * state.vals["UserAttention"]

            # Now, decide on length using reactivity
            length_score = state.vals["UserReactivity"]
        else:
            # Can use data from previous sequences to tune this one
            
            # First, decide on complexity using confusion, engagement and accuracy
            complexity_score = state.vals["UserConfusion"] * state.vals["UserEngagement"] * state.vals["BaseUserAccuracy"]

            # Next, decide on length using response time, accuracy and whether or not the user timed out
            timeout_score = 1 if state.vals["UserTimeout"] else 0
            default_reactivity = 0.8
            default_attention = 0.8
            default_memory = 0.8
            default_time_factor = max(0,min(1,0.4*default_reactivity +0.225*default_memory + 0.15*default_attention + 0.225*state.vals["SequenceComplexity"] + 0.225))
            base_time_gradient = 0.625 * state.vals["SequenceLength"]
            base_min_time = 0.5 * state.vals["SequenceLength"]
            base_time_taken = base_time_gradient * (1 - default_time_factor) + base_min_time
            time_score = max(0,min(1,1-(state.vals["ObservedUserResponseTime"]/base_time_taken)))
            length_score = 0.5*timeout_score + 0.5*state.vals["BaseUserAccuracy"]*time_score

        # Determine actual values
        complexity = round(complexity_score*(CognitiveSequenceState.MAX_COMPLEXITY-CognitiveSequenceState.MIN_COMPLEXITY))+CognitiveSequenceState.MIN_COMPLEXITY
        length = round(length_score*(CognitiveSequenceState.MAX_LENGTH-CognitiveSequenceState.MIN_LENGTH))+CognitiveSequenceState.MIN_LENGTH

        return SetSequenceParametersAction(length, complexity)

    def execute(self, state:CognitiveSequenceState, action:Action):
        if isinstance(action,SetSequenceParametersAction):
            # Update internal state
            state.vals["SequenceComplexity"] = action.sequence_complexity
            state.vals["SequenceLength"] = action.sequence_length
            state.vals["SequenceSet"] = True
            state.vals["NumSequences"] += 1

            # Generate the sequence
            state.vals["CurrentSequence"] = self.generate_sequence(action)

            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
    def generate_sequence(self,action:SetSequenceParametersAction):
        character_set = ["A","B","C","D"]
        allowed_characters = character_set[0:action.sequence_complexity]

        # TODO: If we care about reproducibility here, add a seed variable
        sequence = [np.random.choice(allowed_characters) for _ in range(action.sequence_length)]

        print(f"ROBOT SETS SEQUENCE TO LENGTH {action.sequence_length} AND COMPLEXITY {action.sequence_complexity}")

        return ''.join(sequence)
    
    def input_variables(self):
        return [
            "NumSequences",
            "UserMemory",
            "UserAttention",
            "UserReactivity",
            "UserConfusion",
            "UserEngagement",
            "BaseUserAccuracy",
            "UserTimeout",
            "SequenceComplexity",
            "SequenceLength",
            "ObservedUserResponseTime",
        ]
    
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
        if not state.vals["SequenceSet"]:
            # Sequence not set!
            return py_trees.common.Status.FAILURE

        # Present the sequence to the user
        self.board.environment.provide_sequence(state)

        # Update internal variables
        state.vals["NumRepetitions"] += 1

        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["SequenceSet"]
    
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