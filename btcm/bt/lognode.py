import py_trees

from btcm.dm.action import Action,NullAction

class LogNode:
    def __init__(self,behaviour:py_trees.behaviour.Behaviour,category:str):
        self.name = behaviour.name
        self.category = category
        self.status = py_trees.common.Status.INVALID
        self.action = None
        self.behaviour_class = behaviour.__class__.__name__
        self.behaviour_module = behaviour.__class__.__module__

        self.tick = 0
        self.time = 0

    def to_dict(self) -> dict:
        return {
            "name":self.name,
            "category":self.category,
            "status":str(self.status),
        }
    
    def info_dict(self) -> dict:
        if self.is_leaf():
            return {
                "name":self.name,
                "category":self.category,
                "class":self.behaviour_class,
                "module":self.behaviour_module
            }
        else:
            return {
                "name":self.name,
                "category":self.category,
                "children":[]
            }
    
    def status_dict(self) -> dict:
        if self.is_leaf():
            return {
                "status":str(self.status),
                "action":str(self.action)
            }
        else:
            return {
                "status":str(self.status)
            }

    def log_action(self,action:Action):
        self.action = action

    def is_leaf(self):
        return self.category in ["Action","Condition"]
    
    def update_time(self,tick:int,time:int):
        self.tick = tick
        self.time = time