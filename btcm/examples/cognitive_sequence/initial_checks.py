import py_trees

from btcm.bt.nodes import ActionNode,ConditionNode
from btcm.dm.action import NullAction

from btcm.examples.cognitive_sequence.basic import EndGameAction
from btcm.examples.cognitive_sequence.start_game import start_game_subtree

'''
LEAF NODES
'''
class CheckOverride(ConditionNode):
    def __init__(self, name:str = "CheckOverride"):
        super(CheckOverride, self).__init__(name)

    def execute(self, state, _):
        if state.vals["EndGame"]:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return ["EndGame"]
    
class EndGame(ActionNode):
    def __init__(self, name:str = "EndGame"):
        super(EndGame, self).__init__(name)

        # Requires write access to environment
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def decide(self, _):
        return EndGameAction()

    def execute(self, _, __):
        success = self.board.environment.end_game() # Tell the environment to end the game
        if success:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return []
    
    def action_space(self):
        return [EndGameAction(),NullAction()]
    
'''
Composite Nodes
'''
def initial_checks_subtree():
    check_override_and_end_sequence = py_trees.composites.Sequence(
        name = "CheckOverrideAndEndSequence",
        memory = False,
        children = [
            CheckOverride(),
            EndGame()
        ]
    )

    override_or_continue_fallback = py_trees.composites.Selector(
        name = "OverrideOrContinueFallback",
        memory = False,
        children = [
            check_override_and_end_sequence,
            start_game_subtree()
        ]
    )

    return override_or_continue_fallback