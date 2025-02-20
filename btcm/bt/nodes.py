import py_trees

from typing import List # For type hints

from btcm.dm.state import State
from btcm.dm.action import Action,NullAction
from btcm.bt.lognode import LogNode

class Leaf(py_trees.behaviour.Behaviour):
    '''
    Class for leaf nodes in a PyTrees BT

    '''
    def __init__(self, name: str):
        super().__init__(name)

        # Blackboard
        self.board = self.attach_blackboard_client(name=f"{name}_board")
        self.board.register_key("state", access=py_trees.common.Access.READ)

        # Logging
        self.lognode:LogNode = None

    '''
    EMPTY BOILERPLATE FUNCTIONS
    '''

    def setup(self) -> None:
        pass

    def initialise(self) -> None:
        pass

    def terminate(self, new_status) -> None:
        pass

    '''
    HELPER FUNCTIONS
    '''
    def action_space(self) -> List[Action]:
        '''
        This function returns a list of Actions that can be selected by the decide() function
        '''
        raise NotImplementedError
    
    def input_variables(self) -> List[str]:
        '''
        This function returns a list of State variables (strings as keys) that are used as input by the node
        '''
        raise NotImplementedError

    '''
    BT NODE FUNCTIONALITY
    '''
    def decide(self,state:State) -> Action:
        '''
        This function should map an input State to an appropriate Action
        '''
        raise NotImplementedError
    
    def execute(self,state:State,action:Action) -> py_trees.common.Status:
        '''
        This function should execute the Action in the environment and return a pytrees status
        '''
        raise NotImplementedError
    
    def update(self) -> py_trees.common.Status:
        '''
        This function executes when the node is ticked. 
        It calls the decide() and execute() functions in order. 
        '''
        state = self.board.state
        action = self.decide(state)

        # Logging
        if self.lognode is not None:
            self.lognode.log_action(action)
        
        return self.execute(state,action)
    
    '''
    LOGGING
    '''
    def add_log_node(self,lognode:LogNode):
        self.lognode = lognode

class ActionNode(Leaf):
    def __init__(self, name: str):
        super().__init__(name)
        self.node_type = "Action"

class ConditionNode(Leaf):
    def __init__(self, name: str):
        super().__init__(name)
        self.node_type = "Condition"

    '''
    HELPER FUNCTIONS
    '''
    def action_space(self) -> List[Action]:
        '''
        This function returns a list containing only the NullAction as condition nodes cannot select actions
        '''
        return [NullAction()]
    
    '''
    BT NODE FUNCTIONALITY
    '''
    def decide(self,state:State) -> Action:
        '''
        This always returns the NullAction as condition nodes cannot make decisions
        '''
        return NullAction()

