class State:
    def __init__(self, values: dict):
        if self.valid_state_assignment(values):
            self.vals = values
        else:
            raise ValueError("Invalid values: doesn't match defines ranges")
        
    def __str__(self):
        return str(self.vals)
        
    @property
    def ranges(self) -> dict:
        '''
        Return a mapping from each variable in self.vars() to a list of possible values
        '''
        raise NotImplementedError

    @property
    def vars(self) -> list[str]:
        '''
        Return a list of the state variables that make up the state, as defined by the state dictionary keys
        '''
        return list(self.ranges.keys())
    
    '''
    HELPER FUNCTIONS
    '''
    def valid_state_assignment(self,values: dict) -> bool:
        if values.keys() != self.ranges.keys():
            # Dicts have mismatching keys
            return False
        
        for var in self.ranges:
            if values[var] not in self.ranges[var]:
                # Variable value outside range
                return False
            
        return True