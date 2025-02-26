import py_trees

from typing import Self

from btcm.bt.nodes import ActionNode,ConditionNode
from btcm.dm.state import State
from btcm.dm.action import Action,NullAction

'''
STATE
'''
class ToyState(State):
    def __init__(self,values:dict=None):
        super().__init__(values=values)

    def ranges(self) -> dict:
        return {
            "VarA":[0,1],
            "VarB":[0,1],
            "VarC":[0,1]
        }
    
    def var_funcs(self) -> dict:
        return {
            "VarA":self.func_varA,
            "VarB":self.func_varB,
            "VarC":self.func_varC,
        }
    
    def retrieve_action(self, action_name):
        if action_name == "ActionA":
            return ActionA()
        elif action_name == "ActionB":
            return ActionB()
        elif action_name == "NullAction":
            return NullAction()
    
    '''
    VARIABLE FUNCTIONS
    '''
    def func_varA(self,state:State):
        return state.vals["VarC"]
    
    def func_varB(self,state:State):
        return state.vals["VarB"]
    
    def func_varC(self,state:State):
        return state.vals["VarC"]
    
    def run(self,node:str,state:State):
        return self.var_funcs()[node](state)
    
    '''
    CAUSAL MODEL
    '''
    def cm_edges(self) -> list[tuple[str,str]]:
        return [
            ("VarC","VarA"),
        ]

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
        return [ActionA(),ActionB(),NullAction()]
