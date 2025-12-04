import py_trees

from btcm.bt.nodes import ActionNode,ConditionNode
from btcm.dm.action import Action,NullAction

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState, ResetTimerAction, CheckTimerAction, AssessSequenceAction,EndThisSequenceAction,RepeatThisSequenceAction
from btcm.examples.cognitive_sequence.basic import RecaptureAttentionAction, EndSequenceSocialAction, RepeatSequenceSocialAction, GiveSequenceHintAction
from btcm.examples.cognitive_sequence.handle_task_end import handle_task_end_subtree

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
        if not state.get_value("ResponseTimerActive"):
            return ResetTimerAction()
        # Otherwise, do nothing
        return NullAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        # Reset env timer
        if action == ResetTimerAction():
            self.board.environment.reset_timer(state)

            # Update state
            state.set_value("ResponseTimerActive",True)

            return py_trees.common.Status.SUCCESS
        # If action is NullAction, do nothing
        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["ResponseTimerActive"]
    
    def output_variables(self):
        my_output = ["ResponseTimerActive"]
        env_output = ["UserResponded","UserTimeout"]
        return my_output + env_output
    
    def action_space(self):
        return [ResetTimerAction(),NullAction()]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def detailed_semantic_description(self) -> str:
        return "Resets the timer if ResponseTimerActive is false, setting ResponseTimerActive to True, UserResponded to False and UserTimeout to False. Otherwise does nothing."
    
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
        my_input = []
        env_input = ["ObservedUserResponseTime"]
        return my_input + env_input
    
    def output_variables(self):
        my_ouptut = []
        env_output = ["UserResponded","UserTimeout"]
        return my_ouptut + env_output
    
    def action_space(self):
        return [CheckTimerAction(),NullAction()]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def detailed_semantic_description(self) -> str:
        return "Nudges the environment to check if the user has responded or timed out yet. As a result executing this node, the environment will update the values of the UserResponded and UserTimeout variables."
    
    
class HandleTimerResponse(ActionNode):
    def __init__(self, name:str = "HandleTimerResponse"):
        super(HandleTimerResponse, self).__init__(name)

    def decide(self, state:CognitiveSequenceState):
        # Never takes an action
        return NullAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        # First, check if the user has responded
        if state.get_value("UserResponded"):
            # If so, return success
            state.set_value("ResponseTimerActive",False)
            return py_trees.common.Status.SUCCESS

        # Check if the timer has expired
        if state.get_value("UserTimeout"):
            # If so, return failure
            state.set_value("ResponseTimerActive",False)
            return py_trees.common.Status.FAILURE
        # Otherwise, return running
        return py_trees.common.Status.RUNNING
    
    def input_variables(self):
        return ["UserResponded","UserTimeout"]
    
    def output_variables(self):
        return ["ResponseTimerActive"]
    
    def action_space(self):
        return [NullAction()]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def detailed_semantic_description(self) -> str:
        return "If UserResponded is True, sets ResponseTimerActive to False and succeeds. Otherwise, if UserTimeout is true, sets ResponseTimerActive to False and fails. Otherwise, returns running."
    
    
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
            # TODO: do something here
            return py_trees.common.Status.SUCCESS
        # Should never get here
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return []
    
    def output_variables(self):
        return []
    
    def action_space(self):
        return [AssessSequenceAction(),NullAction()]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def detailed_semantic_description(self) -> str:
        return "Assesses the user sequence. This has no effect on the state. The node always succeeds."
    
    
class HandleUserResponse(ActionNode):
    def __init__(self, name:str = "HandleUserResponse"):
        super(HandleUserResponse, self).__init__(name)

    def decide(self, state:CognitiveSequenceState):
        # Always handle user response
        return NullAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        # Double check that we actually received a response
        if not state.get_value("UserResponded"):
            return py_trees.common.Status.FAILURE
        
        # TODO: Do something here?

        return py_trees.common.Status.SUCCESS
            
    
    def input_variables(self):
        return ["UserResponded"]
    
    def output_variables(self):
        return []
    
    def action_space(self):
        return [NullAction()]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def detailed_semantic_description(self) -> str:
        return "Fails if UserResponded is False, otherwise succeeds."
    

class RepeatOrEnd(ActionNode):
    def __init__(self, name:str = "RepeatOrEnd"):
        super(RepeatOrEnd, self).__init__(name)

    def decide(self, state:CognitiveSequenceState,engagement_threshold = 0.4,frustration_threshold=0.7):
        # First, check if we have exceeded the maximum number of repetitions
        if state.get_value("NumRepetitions") >= CognitiveSequenceState.MAX_NUM_REPETITIONS:
            return EndThisSequenceAction()
        
        # Check if user has responded
        if state.get_value("UserResponded"):
            if state.get_value("UserNumErrors") == 0 or state.get_value("UserNumErrors") == state.ranges()["UserNumErrors"].get_max():
                # Either perfect or really bad, so we need to move on
                return EndThisSequenceAction()
        else:
            # Check if engagement is low
            if state.get_value("UserEngagement") < engagement_threshold and state.get_value("AttemptedReengageUser"):
                # We have already tried to reengage, move on
                return EndThisSequenceAction()
            
        if state.get_value("UserFrustration") > frustration_threshold:
            # User is too frustrated, move on
            return EndThisSequenceAction()
        
        # Otherwise, repeat
        return RepeatThisSequenceAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        if action == EndThisSequenceAction():
            state.set_value("RepeatSequence",False)
            return py_trees.common.Status.SUCCESS
        elif action == RepeatThisSequenceAction():
            state.set_value("RepeatSequence",True)
            return py_trees.common.Status.SUCCESS
        # Should never get here
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return ["NumRepetitions","UserResponded","UserFrustration","UserEngagement","AttemptedReengageUser","UserNumErrors"]
    
    def output_variables(self):
        return ["RepeatSequence"]
    
    def action_space(self):
        return [RepeatThisSequenceAction(),EndThisSequenceAction(),NullAction()]
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def detailed_semantic_description(self) -> str:
        return "Decides whether to end the current task or give the user another attempt at the same sequence. If NumRepetitions >= the maximum number of attempts, the node will select EndThisSequenceAction. Otherwise, if UserResponded is True and UserNumErrors is either 0 or the maximum possible, it selects EndThisSequenceAction. If instead UserEngagement < 0.4 and AttemptedReengageUser is True, it selects EndThisSequenceAction. If UserFrustration > 0.7, it also selects EndThisSequenceAction. In all other cases, it selects RepeatThisSequenceAction. Selecting EndThisSequenceAction sets RepeatSequence to False, while selecting RepeatThisSequenceAction sets it to True. The node always succeeds."

class DecideSocialAction(ActionNode):
    def __init__(self, name:str = "DecideSocialAction"):
        super(DecideSocialAction, self).__init__(name)

        # Requires write access to environment
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def decide(self, state:CognitiveSequenceState, confusion_threshold=0.6, engagement_threshold = 0.4):
        # Check if repeat sequence is set
        if state.get_value("UserResponded"):
            if state.get_value("RepeatSequence"):
                # Repeating - check if user is confused
                if state.get_value("UserConfusion") >= confusion_threshold:
                    return GiveSequenceHintAction()
                if state.get_value("UserEngagement") < engagement_threshold and not state.get_value("AttemptedReengageUser"):
                    # Check if user is not paying attention
                    return RecaptureAttentionAction()
                # Otherwise, just repeat the sequence
                return RepeatSequenceSocialAction()
            else:
                # End the sequence
                return EndSequenceSocialAction()
        else:
            if state.get_value("RepeatSequence"):
                if state.get_value("UserEngagement") < engagement_threshold and not state.get_value("AttemptedReengageUser"):
                    # Repeating - check if user is not paying attention
                    return RecaptureAttentionAction()
                # Otherwise, just repeat the sequence
                return RepeatSequenceSocialAction()
            else:
                # End the sequence
                return EndSequenceSocialAction()
        
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        state.set_value("FeedbackGiven",True)
        if action == GiveSequenceHintAction():
            # Give a hint to the user
            self.board.environment.give_hint(state)
        elif action == RepeatSequenceSocialAction():
            # Repeat the sequence
            self.board.environment.repeat_sequence_social_action(state)
        elif action == EndSequenceSocialAction():
            # End the sequence
            self.board.environment.end_sequence_social_action(state)
        elif action == RecaptureAttentionAction():
            # Recapture attention
            self.board.environment.recapture_attention(state)
            state.set_value("AttemptedReengageUser",True)

        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["UserResponded","RepeatSequence","UserConfusion","UserEngagement","AttemptedReengageUser"]
    
    def output_variables(self):
        return ["AttemptedReengageUser","FeedbackGiven"]
    
    def action_space(self):
        return [GiveSequenceHintAction(),RepeatSequenceSocialAction(),EndSequenceSocialAction(),RecaptureAttentionAction(),NullAction()]

    '''
    SEMANTIC DESCRIPTION
    '''
    def detailed_semantic_description(self) -> str:
        return "Decides on the interaction strategy for the robot to take with the human. If UserResponded and RepeatSequence are true, and UserConfusion >= 0.6, then it selects GiveSequenceHintAction. If UserResponded and RepeatSequence are true, UserEngagement < 0.4 and AttemptedReengageUser is false, it selects RecaptureAttentionAction. If UserResponded is true but RepeatSequence is false, it selects EndSequenceSocialAction. Otherwise, if UserResponded is not true, and RepeatSequence is True, and UserEngagement < 0.4 and AttemptedReengageUser is false, it selects RecaptureAttentionAction. Otherwise, if UserResponded is not true and RepeatSequence is true, it selects RepeatSequenceSocialAction. In all other cases it selects EndSequenceSocialAction. If RecaptureAttentionAction is selected, then AttemptedReengageUser is set to True. Executing this node always sets FeedbackGiven to True. The node always succeeds."

'''
Composite Nodes
'''
def decide_repeat_and_social_action_sequence():
    return py_trees.composites.Sequence(
        name="DecideRepeatAndSocialAction",
        memory=True,
        children=[
            RepeatOrEnd(),
            DecideSocialAction()
        ]
    )

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
            decide_repeat_and_social_action_sequence()
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
            decide_repeat_and_social_action_sequence()
        ]
    )

    handle_response_and_end_repitition_sequence = py_trees.composites.Sequence(
        name="HandleResponseAndEndRepetition",
        memory=True,
        children=[
            handle_response_or_no_response_fallback,
            handle_task_end_subtree()
        ]
    )

    return handle_response_and_end_repitition_sequence