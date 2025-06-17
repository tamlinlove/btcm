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

    def execute(self, state:CognitiveSequenceState, _):
        if state.get_value("NumRepetitions") == 0:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return ["NumRepetitions"]
    
    def output_variables(self):
        return []
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_description(self) -> str:
        return "Checks if a sequence has already been set or not. If not, it returns SUCCESS, otherwise FAILURE."
    
class SetSequenceParameters(ActionNode):
    def __init__(self, name:str = "SetSequenceParameters"):
        super(SetSequenceParameters, self).__init__(name)

        self.board.register_key("display", access=py_trees.common.Access.READ)

    def decide(self, state:CognitiveSequenceState):
        # Initialise difficulty parameters
        if state.get_value("NumSequences") == 0:
            # This is the very first parameter setting, always start with the same length and complexity
            length = round(0.3*(CognitiveSequenceState.MAX_LENGTH-CognitiveSequenceState.MIN_LENGTH)) + CognitiveSequenceState.MIN_LENGTH
            complexity = round(0.5*(CognitiveSequenceState.MAX_COMPLEXITY-CognitiveSequenceState.MIN_COMPLEXITY)) + CognitiveSequenceState.MIN_COMPLEXITY
        else:
            # Can use data from previous sequences to tune this one
           
            # First, decide on complexity using confusion and number of errors
            complexity = state.get_value("SequenceComplexity")
            length = state.get_value("SequenceLength")

            # Add/Subtract based on number of errors
            complexity -= state.get_value("UserNumErrors")-1

            # Add/Subtract based on confusion
            if state.get_value("UserConfusion") >= 0.7:
                complexity -= 1
            elif state.get_value("UserConfusion") < 0.3:
                complexity += 1

            complexity = min(CognitiveSequenceState.MAX_COMPLEXITY,max(CognitiveSequenceState.MIN_COMPLEXITY,complexity))

            # Now do length, based on response time, accuracy and timeout

            
            if state.get_value("UserTimeout"):
                # Halve length if timeout
                length = round(0.5*length)
            else:
                # Otherwise, add/subtract based on response time
                expected_time = 0.8*state.get_value("SequenceLength")
                time_diff = expected_time - state.get_value("ObservedUserResponseTime")
                length += round(min(2,max(-2,time_diff)))

                # Add/subtract based on number of errors
                length -= state.get_value("UserNumErrors")-1

            length = min(CognitiveSequenceState.MAX_LENGTH,max(CognitiveSequenceState.MIN_LENGTH,length))

        return SetSequenceParametersAction(length, complexity)

    def execute(self, state:CognitiveSequenceState, action:Action):
        if isinstance(action,SetSequenceParametersAction):
            # Update internal state
            state.set_value("SequenceComplexity",action.sequence_complexity)
            state.set_value("SequenceLength",action.sequence_length)
            state.set_value("SequenceSet",True)
            state.increment("NumSequences")

            # Generate the sequence
            state.set_value("CurrentSequence",self.generate_sequence(state,action))

            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
    def generate_sequence(self,state:CognitiveSequenceState,action:SetSequenceParametersAction):
        character_set = ["A","B","C","D"]
        allowed_characters = character_set[0:action.sequence_complexity]

        # TODO: If we care about reproducibility here, add a seed variable
        rng = np.random.default_rng(0)
        sequence = [rng.choice(allowed_characters) for _ in range(action.sequence_length)]

        if self.board.display:
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
            "UserNumErrors",
            "UserTimeout",
            "SequenceComplexity",
            "SequenceLength",
            "ObservedUserResponseTime",
        ]
    
    def output_variables(self):
        return ["SequenceLength","SequenceComplexity","SequenceSet","NumSequences","CurrentSequence"]

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
        if state.get_value("SequenceSet"):
            return NullAction()
        return CrashAction()
    
    def execute(self, _, action:Action):
        if action == CrashAction():
            return py_trees.common.Status.FAILURE
        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["SequenceSet"]
    
    def output_variables(self):
        return []
    
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
        if not state.get_value("SequenceSet"):
            # Sequence not set!
            return py_trees.common.Status.FAILURE

        # Present the sequence to the user
        self.board.environment.provide_sequence(state)

        # Update internal variables
        state.increment("NumRepetitions")

        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        my_input = ["SequenceSet","NumRepetitions"]
        env_input = ["SequenceLength","SequenceComplexity","UserMemory","UserAttention","UserReactivity","AccuracySeed","ResponseTimeSeed"]
        return my_input + env_input
    
    def output_variables(self):
        my_output = ["NumRepetitions"]
        env_output = ["UserResponded","UserConfusion","UserEngagement","BaseUserAccuracy","UserNumErrors","BaseUserResponseTime","ObservedUserResponseTime","UserSequence","AccuracySeed","ResponseTimeSeed"]
        return my_output + env_output
    
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