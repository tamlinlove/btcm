from btcm.cm.causalmodel import CausalModel,CausalNode
from btcm.bt.state import State

from typing import Dict
from collections.abc import Callable

class StateNode(CausalNode):
    def __init__(self, name, vals, func, value):
        super().__init__(name=name, vals=vals, func=func, value=value)

        self.category = "State"

class StateModel(CausalModel):
    def __init__(self,state:State,var_funcs:Dict[str,Callable]):
        super().__init__()

        self.state = state
        self.var_funcs = var_funcs

        for var in self.state.vals:
            node = StateNode(
                name=var,
                vals=self.state.ranges[var],
                func=self.var_funcs[var],
                value=self.state.vals[var]
            )
            self.add_node(node)



