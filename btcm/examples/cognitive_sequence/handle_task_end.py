import py_trees

from btcm.bt.nodes import ActionNode,ConditionNode
from btcm.dm.action import Action,NullAction

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState
from btcm.examples.cognitive_sequence.basic import EndThisSequenceAction,RepeatThisSequenceAction

'''
LEAF NODES
'''
class CheckEndCurrentSequence(ConditionNode):
    def __init__(self, name:str = "CheckEndCurrentSequence"):
        super(CheckEndCurrentSequence, self).__init__(name)

    def execute(self, state:CognitiveSequenceState, _):
        # Check if the current sequence is over
        return py_trees.common.Status.SUCCESS if not state.get_value("RepeatSequence") else py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return ["RepeatSequence"]

class EndCurrentSequence(ActionNode):
    def __init__(self, name:str = "EndCurrentSequence"):
        super(EndCurrentSequence, self).__init__(name)

        # Requires write access to environment
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def decide(self, _):
        # Always ends the current sequence
        return EndThisSequenceAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        # End the current sequence, reset for new sequence
        state.set_value("NumRepetitions",0)
        state.set_value("SequenceSet",False)
        state.set_value("ResponseTimerActive",False)
        state.set_value("AttemptedReengageUser",False)
        state.set_value("RepeatSequence",False)

        # Check if we have reached the maximum number of sequences
        if state.get_value("NumSequences") >= state.MAX_NUM_SEQUENCES:
            state.set_value("EndGame",True)

        # To help with reading terminal output
        print("---------------")

        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["NumSequences"]
    
    def action_space(self):
        return [EndThisSequenceAction(),NullAction()]
    
class RepeatCurrentSequence(ActionNode):
    def __init__(self, name:str = "RepeatCurrentSequence"):
        super(RepeatCurrentSequence, self).__init__(name)

    def decide(self, _):
        # Always repeats the current sequence
        return RepeatThisSequenceAction()
    
    def execute(self, state:CognitiveSequenceState, action:Action):
        # TODO: If there is any logic to handle repeated sequences, put it here

        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return []
    
    def action_space(self):
        return [EndThisSequenceAction(),NullAction()]
    
'''
COMPOSITE NODES
'''
def handle_task_end_subtree():
    check_end_and_end_sequence = py_trees.composites.Sequence(
        name = "CheckEndAndEndSequence",
        memory = False,
        children = [
            CheckEndCurrentSequence(),
            EndCurrentSequence()
        ]
    )

    end_or_repeat_fallback = py_trees.composites.Selector(
        name = "EndOrRepeatFallback",
        memory = False,
        children = [
            check_end_and_end_sequence,
            RepeatCurrentSequence()
        ]
    )

    return end_or_repeat_fallback
    