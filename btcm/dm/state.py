class State:
    def __init__(self, values: dict):
        if self.valid_state_assignment(values):
            self.vals = values
        else:
            raise ValueError("Invalid values: doesn't match defines ranges")
        
    def __str__(self):
        return str(self.vals)
        
    @staticmethod
    def ranges() -> dict:
        '''
        Return a mapping from each variable in self.vars() to a list of possible values
        '''
        raise NotImplementedError
    
    @staticmethod
    def var_funcs() -> dict:
        '''
        Return a mapping from each variable in self.vars() to a function used to compute that variable's value
        '''
        raise NotImplementedError

    def vars(self) -> list[str]:
        '''
        Return a list of the state variables that make up the state, as defined by the state dictionary keys
        '''
        return list(self.ranges().keys())
    
    def set_value(self,var:str,value):
        if not self.valid_var_value(var,value):
            raise ValueError(f"Cannot set {var} to {value}")
        
        self.vals[var] = value
    
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
