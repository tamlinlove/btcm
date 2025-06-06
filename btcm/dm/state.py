from typing import Self,Dict

from btcm.dm.action import Action

class VarRange:
    def __init__(self,range_type:str="cat",values:list=None,var_type:type=None,min:float=None,max:float=None):
        self.range_type = range_type
        self.values = values
        self.var_type = var_type
        self.min = min
        self.max = max

    '''
    Constructors
    '''
    @staticmethod
    def normalised_float():
        return VarRange(range_type="cont",var_type=float,min=0,max=1)
    
    @staticmethod
    def categorical(values:list):
        return VarRange(range_type="cat",values=values)
    
    @staticmethod
    def boolean():
        return VarRange(range_type="bool",values=[True,False],var_type=bool)
    
    @staticmethod
    def int_range(min:int,max:int):
        if min>max:
            raise ValueError(f"Minimum {min} must be smaller than or equal to maximum {max}")
        
        return VarRange(range_type="cat",values=list(range(min,max+1)),var_type=int,min=min,max=max)
    
    @staticmethod
    def float_range(min:float,max:float):
        if min>max:
            raise ValueError(f"Minimum {min} must be smaller than or equal to maximum {max}")
        
        return VarRange(range_type="cont",var_type=float,min=min,max=max)
    
    @staticmethod
    def discretised_float_range(min:float,max:float,step:float,dec_places:int=10):
        if min>max:
            raise ValueError(f"Minimum {min} must be smaller than or equal to maximum {max}")

        float_range = [round(min + i * step, dec_places) for i in range(int((max - min) / step) + 1)]
        return VarRange(range_type="disc_cont",values=float_range,var_type=float,min=min,max=max)
    
    @staticmethod
    def any_string():
        return VarRange(range_type="any",var_type=str)
    
    @staticmethod
    def any_int():
        return VarRange(range_type="any",var_type=int)
    
    '''
    Utility
    '''
    def get_max(self):
        if self.max is None:
            raise TypeError(f"Cannot get max value for VarRange type {self.range_type}")
        else:
            return self.max
        
    def get_middle_value(self):
        if self.values is None:
            raise TypeError(f"Cannot get median value for VarRange type {self.range_type}")
        else:
            middleIndex = (len(self.values) - 1)//2
            return self.values[middleIndex] 
    
    '''
    Checks
    '''
    def valid(self,value):
        # First, check typing
        if self.var_type is not None:
            # var_type = None allows any type
            if self.var_type == float:
                # Allow floats and ints
                if not isinstance(value,(float,int)):
                    print(f"Value {value} of type {type(value)} is not of type {self.var_type}")
                    return False
            elif not type(value) is self.var_type:
                # For others, must match type exactly
                print(f"Value {value} of type {type(value)} is not of type {self.var_type}")
                return False
            

        if self.range_type in ["cont","disc_cont"]:
            # Continuous between a min and max
            return value >= self.min and value <= self.max
        elif self.range_type in ["cat","bool"]:
            # Categorical, can check values
            return value in self.values
        elif self.range_type == "any":
            # Allows any variable of the right type
            return True
        else:
            raise ValueError(f"Unrecognised VarRange type {self.range_type}")
    

class State:
    def __init__(self,values:dict=None):
       self.range_dict = self.get_range_dict()

       self.vals = None
       if values is not None:
           self.set_values(values)

    @classmethod
    def copy_state(cls,state:Self) -> Self:
        return cls(values=state.vals)
        
    def __str__(self):
        return str(self.vals)
    
    '''
    VARIABLE INFO
    '''

    def get_range_dict(self) -> Dict[str,VarRange]:
        '''
        Return a mapping from each variable in self.vars() to a corresponding VarRange object
        '''
        raise NotImplementedError
        
    def ranges(self) -> Dict[str,VarRange]:
        return self.range_dict
    
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
    
    def internal(self,var:str) -> bool:
        '''
        Return a bool, where True indicates the variable is internal to the BT, and False external
        '''
        raise NotImplementedError

    
    '''
    ACTION INFO
    '''
    @staticmethod
    def retrieve_action(action_name:str) -> Action:
        '''
        Given a string id of an action, return an Action object
        '''
        raise NotImplementedError
    
    '''
    VALUES
    '''
     
    def set_values(self,values:dict):
        if self.valid_state_assignment(values):
            self.vals = values
        else:
            raise ValueError("Invalid values: doesn't match defined ranges")
    
    def set_value(self,var:str,value):
        if not self.ranges()[var].valid(value):
            raise ValueError(f"Cannot set {var} to {value}")
        
        self.vals[var] = value

    def get_values(self,nodes:list[str]=None):
        if nodes is None:
            return self.vals
        else:
            return {node:self.vals[node] for node in nodes}
        
    def get_value(self,node:str):
        return self.vals[node]
    
    def increment(self,node:str,increment_step:float=1):
        new_value = self.get_value(node) + increment_step
        if self.ranges()[node].valid(new_value):
            self.vals[node] = new_value
        else:
            # Cannot increment, leave the variable as it is
            pass

    '''
    CAUSAL MODEL
    '''
    def cm_edges(self) -> list[tuple[str,str]]:
        '''
        Return a list of edges representing the assumptions of a causal model modelling this state
        '''
        return []
    
    def run(self,node:str,*args,**kwargs):
        '''
        Given the name of the node, run its function and return its new value based on other arguments
        '''
        raise NotImplementedError
    
    def can_intervene(self,node:str):
        '''
        Given the name of the node, return True if a causal model is allowed to intervene on its value
        '''
        raise NotImplementedError
    
    '''
    HELPER FUNCTIONS
    '''
    def valid_state_assignment(self,values: dict) -> bool:
        if values.keys() != self.ranges().keys():
            # Dicts have mismatching keys
            return False
        
        for var in self.ranges():
            valid = self.ranges()[var].valid(values[var])
            if not valid:
                print(f"Invalid value for {var}: {values[var]}")
                return False
            
        return True
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_dict(self) -> dict[str,str]:
        return {var:"A state variable" for var in self.vars()}
    
    '''
    INFORMATION FOR LOGGING
    '''
    def info_dict(self) -> dict:
        semantics = self.semantic_dict()
        internals = self.internal()

        info = {"internal":{},"external":{}}
        for var in self.vars():
            int_text = "internal" if internals[var] else "external"
            info[int_text][var] = semantics[var]

        return info
