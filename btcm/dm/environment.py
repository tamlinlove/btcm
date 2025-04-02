from btcm.dm.state import State

class Environment:
    def __init__(self,state:State):
        self.observed_state = state