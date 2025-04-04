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
    
class WaitForUserReponse(ActionNode):
    def __init__(self, name:str = "WaitForUserReponse"):
        super(WaitForUserReponse, self).__init__(name)

        # Requires write access to environment and state
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def decide(self, state:CognitiveSequenceState):
        # Always checks timer
        return CheckTimerAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        if action == CheckTimerAction():
            # Check with the environment
            self.board.environment.check_timer(state)

            print("User response time: ", state.vals["UserResponseTime"], "Responded: ", state.vals["UserResponded"])

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
        # Shouldn't ever be any other kind of action
        return py_trees.common.Status.FAILURE


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
            WaitForUserReponse()
        ]
    )

    return start_timer_and_wait_sequence