import py_trees

from btcm.bt.nodes import ActionNode,ConditionNode
from btcm.dm.action import Action,NullAction

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState, ResetTimerAction, CheckTimerAction, AssessSequenceAction

'''
LEAF NODES
'''
class StartResponseTimer(ActionNode):
    def __init__(self, name:str = "StartResponseTimer"):
        super(StartResponseTimer, self).__init__(name)

        # Requires write access to environment and state
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)
        self.board.register_key("state", access=py_trees.common.Access.WRITE)

    def decide(self, state:CognitiveSequenceState):
        # If the timer is not active, start it
        if not state.vals["ResponseTimerActive"]:
            return ResetTimerAction()
        # Otherwise, do nothing
        return NullAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        # Reset env timer
        if action == ResetTimerAction():
            status = self.board.environment.reset_timer()
            if status:
                state.vals["ResponseTimerActive"] = True
                return py_trees.common.Status.SUCCESS
            return py_trees.common.Status.FAILURE
        # If action is NullAction, do nothing
        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["ResponseTimerActive"]
    
    def action_space(self):
        return [ResetTimerAction(),NullAction()]
    
class NudgeTimer(ActionNode):
    def __init__(self, name:str = "NudgeTimer"):
        super(NudgeTimer, self).__init__(name)

        # Requires write access to environment
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def decide(self, state:CognitiveSequenceState):
        # Always nudges timer
        return CheckTimerAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        if action == CheckTimerAction():
            # Check with the environment
            self.board.environment.check_timer(state)
            return py_trees.common.Status.SUCCESS
        # Should never get here
        return py_trees.common.Status.FAILURE

    def input_variables(self):
        return []
    
    def action_space(self):
        return [CheckTimerAction(),NullAction()]
    
class HandleTimerResponse(ActionNode):
    def __init__(self, name:str = "HandleTimerResponse"):
        super(HandleTimerResponse, self).__init__(name)

        # Requires write access to environment
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def decide(self, state:CognitiveSequenceState):
        # Never takes an action
        return NullAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        # First, check if the user has responded
        if state.vals["UserResponded"]:
            # If so, return success
            state.vals["ResponseTimerActive"] = False
            return py_trees.common.Status.SUCCESS

        # Check if the timer has expired
        if state.vals["UserResponseTime"] >= state.MAX_TIMEOUT:
            # If so, return failure
            return py_trees.common.Status.FAILURE
        # Otherwise, return running
        return py_trees.common.Status.RUNNING
    
    def input_variables(self):
        return ["UserResponded","UserResponseTime"]
    
    def action_space(self):
        return [NullAction()]
    
class AssessUserSequence(ActionNode):
    def __init__(self, name:str = "AssessUserSequence"):
        super(AssessUserSequence, self).__init__(name)

        # Requires read access to environment and state
        self.board.register_key("environment", access=py_trees.common.Access.READ)

    def decide(self, state:CognitiveSequenceState):
        # Always assess the user sequence
        return AssessSequenceAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        if action == AssessSequenceAction():
            # Check with the environment
            self.board.environment.assess_user_sequence(state)
            return py_trees.common.Status.SUCCESS
        # Should never get here
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return []
    
    def action_space(self):
        return [AssessSequenceAction(),NullAction()]
    
class HandleUserResponse(ActionNode):
    def __init__(self, name:str = "HandleUserResponse"):
        super(HandleUserResponse, self).__init__(name)

    def decide(self, state:CognitiveSequenceState):
        # Always handle user response
        return NullAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        # Double check that we actually received a response
        if not state.vals["UserResponded"]:
            return py_trees.common.Status.FAILURE
        
        # Update the user speed and accuracy estimates based on latest response
        # First, update speed
        if state.vals["LatestUserSpeed"] == "Faster":
            # User faster than expected given difficulty
            if state.vals["UserSpeed"] == "Slow":
                state.vals["UserSpeed"] = "Medium"
            elif state.vals["UserSpeed"] == "Medium":
                state.vals["UserSpeed"] = "Fast"
        elif state.vals["LatestUserSpeed"] == "Normal":
            # User normal speed given difficulty
            if state.vals["UserSpeed"] == "Slow":
                state.vals["UserSpeed"] = "Medium"
        else:
            # User slower than expected given difficulty
            if state.vals["UserSpeed"] == "Fast":
                state.vals["UserSpeed"] = "Medium"
            elif state.vals["UserSpeed"] == "Medium":
                state.vals["UserSpeed"] = "Slow"

        # Now, update accuracy
        if state.vals["LatestUserAccuracy"] == "Perfect":
            # Improve user accuracy
            if state.vals["UserAccuracy"] == "Low":
                state.vals["UserAccuracy"] = "Medium"
            elif state.vals["UserAccuracy"] == "Medium":
                state.vals["UserAccuracy"] = "High"
        elif state.vals["LatestUserAccuracy"] == "Good":
            # Improve user accuracy
            if state.vals["UserAccuracy"] == "Low":
                state.vals["UserAccuracy"] = "Medium"
            elif state.vals["UserAccuracy"] == "Medium":
                state.vals["UserAccuracy"] = "High"
        elif state.vals["LatestUserAccuracy"] == "Medium":
            # Move user accuracy to medium
            state.vals["UserAccuracy"] = "Medium"
        elif state.vals["LatestUserAccuracy"] == "Poor":
            # Decrease user accuracy
            if state.vals["UserAccuracy"] == "High":
                state.vals["UserAccuracy"] = "Medium"
            elif state.vals["UserAccuracy"] == "Medium":
                state.vals["UserAccuracy"] = "Low"
        else:
            # Very bad performance, straight to bottom
            state.vals["UserAccuracy"] = "Low"

        return py_trees.common.Status.SUCCESS
            
    
    def input_variables(self):
        return ["UserResponded","LatestUserSpeed","LatestUserAccuracy","UserSpeed","UserAccuracy"]
    
    def action_space(self):
        return [NullAction()]
    
class DecideNextSteps(ActionNode):
    def __init__(self, name:str = "DecideNextSteps"):
        super(DecideNextSteps, self).__init__(name)

        # Requires read access to environment and state
        self.board.register_key("environment", access=py_trees.common.Access.READ)

    def decide(self, state:CognitiveSequenceState):
        # TODO: Implement
        return NullAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        # TODO: Implement
        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return []
    
    def action_space(self):
        return [NullAction()]

'''
Composite Nodes
'''
def handle_user_response_subtree():
    # Create the composite node
    nudge_timer_and_handle_response_sequence = py_trees.composites.Sequence(
        name="NudgeTimerAndHandleResponse",
        memory=False, # Needs to be false in order to always check for timer updates
        children=[
            NudgeTimer(),
            HandleTimerResponse()
        ]
    )

    start_timer_and_wait_sequence = py_trees.composites.Sequence(
        name="StartTimerAndWait",
        memory=True,
        children=[
            StartResponseTimer(),
            nudge_timer_and_handle_response_sequence
        ]
    )

    assess_sequence_and_handle_sequence = py_trees.composites.Sequence(
        name="AssessSequenceAndHandleUserResponse",
        memory=True,
        children=[
            AssessUserSequence(),
            HandleUserResponse(),
            DecideNextSteps()
        ]
    )

    wait_and_handle_response_sequence = py_trees.composites.Sequence(
        name="WaitAndHandleResponse",
        memory=True,
        children=[
            start_timer_and_wait_sequence,
            assess_sequence_and_handle_sequence
        ]
    )

    handle_response_or_no_response_fallback = py_trees.composites.Selector(
        name="HandleResponseOrNoResponseFallback",
        memory=True,
        children=[
            wait_and_handle_response_sequence,
            DecideNextSteps()
        ]
    )

    return handle_response_or_no_response_fallback