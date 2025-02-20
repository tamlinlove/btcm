import py_trees

from btcm.dm.action import Action,NullAction

class LogNode:
    def __init__(self,name:str,category:str):
        self.name = name
        self.category = category
        self.status = py_trees.common.Status.INVALID
        self.action = None

        self.tick = 0
        self.time = 0

    def to_dict(self) -> dict:
        return {
            "name":self.name,
            "category":self.category,
            "status":str(self.status),
        }
    
    def log_action(self,action:Action):
        self.action = action

    def is_leaf(self):
        return self.category in ["Action","Condition"]
    
    def update_time(self,tick:int,time:int):
        self.tick = tick
        self.time = time