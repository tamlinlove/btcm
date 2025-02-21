from btcm.dm.action import Action

class State:
    def __init__(self,values:dict=None):
       self.vals = None
       if values is not None:
           self.set_values(values)
        
    def __str__(self):
        return str(self.vals)
        
    def ranges(self) -> dict:
        '''
        Return a mapping from each variable in self.vars() to a list of possible values
        '''
        raise NotImplementedError
    
    def var_funcs(self) -> dict:
        '''
        Return a mapping from each variable in self.vars() to a function used to compute that variable's value
        '''
        raise NotImplementedError

    def vars(self) -> list[str]:
        '''
        Return a list of the state variables that make up the state, as defined by the state dictionary keys
        '''
        return list(self.ranges().keys())
    
    def retrieve_action(self,action_name:str) -> Action:
        '''
        Given a string id of an action, return an Action object
        '''
        raise NotImplementedError
     
    def set_values(self,values:dict):
        if self.valid_state_assignment(values):
            self.vals = values
        else:
            raise ValueError("Invalid values: doesn't match defines ranges")
    
    def set_value(self,var:str,value):
        if not self.valid_var_value(var,value):
            raise ValueError(f"Cannot set {var} to {value}")
        
        self.vals[var] = value

    '''
    CAUSAL MODEL
    '''
    def cm_edges(self) -> list[tuple[str,str]]:
        '''
        Return a list of edges representing the assumptions of a causal model modelling this state
        '''
        return []
    
    '''
    HELPER FUNCTIONS
    '''
    def valid_state_assignment(self,values: dict) -> bool:
        if values.keys() != self.ranges().keys():
            # Dicts have mismatching keys
            return False
        
        for var in self.ranges():
            valid = self.valid_var_value(var,values[var])
            if not valid:
                return False
            
        return True
    
    def valid_var_value(self,var:str,value) -> bool:
        if value not in self.ranges()[var]:
            # Variable value outside range
            return False
        return True
