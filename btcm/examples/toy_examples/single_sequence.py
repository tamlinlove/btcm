import py_trees

from btcm.bt.nodes import ActionNode,ConditionNode
from btcm.bt.state import State
from btcm.bt.action import Action

'''
STATE
'''
class ToyState(State):
    def __init__(self, assignment):
        super().__init__(assignment)

    @property
    def ranges(self) -> dict:
        return {
            "VarA":[0,1],
            "VarB":[0,1],
            "VarC":[0,1]
        }

'''
ACTIONS
'''
class ActionA(Action):
    name = "ActionA"

    def __init__(self):
        super().__init__()

class ActionB(Action):
    name = "ActionB"

    def __init__(self):
        super().__init__()


'''
BLACKBOARD
'''
def setup_board(vals):
    board = py_trees.blackboard.Client(name="Board")
    board.register_key("state", access=py_trees.common.Access.WRITE)
    state = ToyState(vals)
    board.state = state

    return board

'''
BT ROOT
'''

def make_tree():
    root = py_trees.composites.Sequence(
        name = "SingleSequence",
        memory = False,
        children = [
            ToyGuard(),
            ToyAction()
        ]
    )

    tree = py_trees.trees.BehaviourTree(root=root)
    return tree

'''
NODES IN THE BT
'''

class ToyGuard(ConditionNode):
    '''
    TODO
    '''
    def __init__(self, name : str = "ToyGuard"):
        super(ToyGuard, self).__init__(name)

    def execute(self, state, _):
        if state.vals["VarA"] == state.vals["VarB"]:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return ["VarA","VarB"]

class ToyAction(ActionNode):
    '''
    TODO
    '''
    def __init__(self, name : str = "ToyAction"):
        super(ToyAction, self).__init__(name)

    def decide(self, state):
        if state.vals["VarB"] == 0:
            return ActionA()
        else:
            return ActionB()

    def execute(self, _, action):
        if action == ActionA:
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE 
        
    def input_variables(self):
        return ["VarB"]
    
    def action_space(self):
        return [ActionA(),ActionB()]
