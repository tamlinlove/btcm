class Action:
    def __init__(self):
        pass

    def __str__(self):
        return self.name
    
    @property
    def name(self) -> str:
        raise NotImplementedError

class NullAction(Action):

    name = "NullAction"

    def __init__(self):
        pass