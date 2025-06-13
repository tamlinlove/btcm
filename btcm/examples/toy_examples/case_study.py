import numpy as np
import py_trees
import time

from typing import Self

from btcm.dm.state import State,VarRange
from btcm.dm.action import Action,NullAction
from btcm.bt.nodes import ActionNode,ConditionNode




'''

STATE

'''

class CaseStudyState(State):
    def __init__(self, values = None):
        super().__init__(values)

    '''
    VARIABLES
    '''
    def get_range_dict(self) -> dict:
        return {
            "X_a": VarRange.boolean(),
            "X_b": VarRange.boolean(),
            "X_c": VarRange.boolean(),
            "X_d": VarRange.boolean(),
        }
    
    def internal(self,var):
        internals = [
            "X_b"
        ]

        return var in internals
    
    '''
    VARIABLE FUNCTIONS
    '''
    def var_funcs(self) -> dict:
        # Most variables don't have a special function...
        func_dict = {
            key: (lambda key: lambda state: state.get_value(key))(key)
            for key in self.ranges().keys()
        }

        # ...but some do:
        func_dict["X_c"] = self.get_x_c
        func_dict["X_d"] = self.get_x_d

        return func_dict
    
    @staticmethod
    def get_x_c(state:Self) -> bool:
        X_c = state.get_value("X_a") and state.get_value("X_b")
        return X_c
    
    @staticmethod
    def get_x_d(state:Self) -> bool:
        X_d = not state.get_value("X_b")
        return X_d
    
    '''
    EXECUTION
    '''
    def run(self,node:str,state:State):
        return self.var_funcs()[node](state)
    
    '''
    ACTIONS
    '''
    @staticmethod
    def retrieve_action(action_name):
        if action_name == "NullAction":
            return NullAction()
        elif action_name == "Action0":
            return Action0()
        elif action_name == "Action1":
            return Action1()
        elif action_name == "Action2":
            return Action2()
        
    '''
    VALUES
    '''
        
    @staticmethod
    def default_values():
        return {
            "X_a":True,
            "X_b":True,
            "X_c":True,
            "X_d":False,
        }
    
    '''
    CAUSAL MODEL
    '''
    def cm_edges(self) -> list[tuple[str,str]]:
        return [
            ("X_a","X_c"),
            ("X_b","X_c"),
            ("X_b","X_d"),
        ]
    
    def can_intervene(self, node):
        return True
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_dict(self) -> dict[str,str]:
        return {
            "X_a":"A boolean variable",
            "X_b":"A boolean variable",
            "X_c":"A boolean variable",
            "X_d":"A boolean variable",
        }
    

'''

ACTIONS

'''
class Action0(Action):
    name = "Action0"

    def __init__(self):
        super().__init__()

class Action1(Action):
    name = "Action1"

    def __init__(self):
        super().__init__()

class Action2(Action):
    name = "Action2"

    def __init__(self):
        super().__init__()

'''

BT

'''
class L0(ConditionNode):
    def __init__(self, name:str = "L0"):
        super(L0, self).__init__(name)

    def execute(self, state:CaseStudyState, _):
        if state.get_value("X_a"):
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return ["X_a"]
    
    def output_variables(self):
        return []
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_description(self) -> str:
        return "A condition node"
    
class L1(ActionNode):
    def __init__(self, name:str = "L1"):
        super(L1, self).__init__(name)

    def decide(self, state:CaseStudyState):
        if state.get_value("X_c"):
            return Action1()
        elif state.get_value("X_a"):
            return Action0()
        else:
            return NullAction()
    
    def execute(self, state:CaseStudyState, action:Action):
        if action == Action0():
            state.set_value("X_b",True)
            state.set_value("X_d",CaseStudyState.get_x_d(state))
        elif action == Action1():
            state.set_value("X_b",False)
            print(CaseStudyState.get_x_d(state))
            state.set_value("X_d",CaseStudyState.get_x_d(state))
        else:
            # Do nothing
            return py_trees.common.Status.FAILURE
        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["X_a","X_c"]
    
    def output_variables(self):
        return ["X_b"]
    
    def action_space(self):
        return [Action0(),Action1(),NullAction()]
    
class L2(ActionNode):
    def __init__(self, name:str = "L2"):
        super(L2, self).__init__(name)

    def decide(self, state:CaseStudyState):
        if state.get_value("X_d"):
            return Action2()
        else:
            return NullAction()
    
    def execute(self, state:CaseStudyState, action:Action):
        if action == Action2():
            state.set_value("X_b",True)
        else:
            # Do nothing
            return py_trees.common.Status.FAILURE
        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["X_d"]
    
    def output_variables(self):
        return ["X_b"]
    
    def action_space(self):
        return [Action2(),NullAction()]
    
def case_study_tree():
    case_study_sequence = py_trees.composites.Sequence(
        name = "CaseStudySequence",
        memory = False,
        children = [
            L0(),
            L1()
        ]
    )

    case_study_fallback = py_trees.composites.Selector(
        name = "CaseStudyFallback",
        memory = False,
        children = [
            case_study_sequence,
            L2()
        ]
    )

    return case_study_fallback

'''

SETUP

'''
def setup_board(vals:dict=None):
    board = py_trees.blackboard.Client(name="Board")
    board.register_key("state", access=py_trees.common.Access.WRITE)

    # State
    if vals is None:
        vals = CaseStudyState.default_values()
    state = CaseStudyState(vals)
    board.state = state

    return board

def make_tree():
    return py_trees.trees.BehaviourTree(root=case_study_tree())

def run(tree:py_trees.trees.BehaviourTree,display_tree:bool=False):
    tree.setup()
    try:
        # Tick the tree
        tree.tick()
        # Sleep for a bit to simulate time passing
        time.sleep(0.1)
        # Optional, print the tree structure
        if display_tree:
            print(py_trees.display.unicode_tree(tree.root, show_status=True))
    except KeyboardInterrupt:
        print("KILL")
        pass