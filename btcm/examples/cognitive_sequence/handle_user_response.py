import py_trees

from btcm.bt.nodes import ActionNode,ConditionNode
from btcm.dm.action import Action,NullAction

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState, ResetTimerAction, CheckTimerAction

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
        print(state.vals["UserResponded"], state.vals["UserResponseTime"])
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

'''
Composite Nodes
'''
def handle_user_response_subtree():
    # Create the composite node
    start_timer_and_wait_sequence = py_trees.composites.Sequence(
        name="HandleUserResponse",
        memory=True,
        children=[
            StartResponseTimer(),
            # TODO: Put Nudge and handle in a sequence without memory
            NudgeTimer(),
            HandleTimerResponse()
        ]
    )

    return start_timer_and_wait_sequence