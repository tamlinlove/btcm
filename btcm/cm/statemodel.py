from btcm.cm.causalmodel import CausalModel,CausalNode
from btcm.bt.state import State

from typing import Dict
from collections.abc import Callable

class StateNode(CausalNode):
    def __init__(self, name, vals, func, value):
        super().__init__(name=name, vals=vals, func=func, value=value)

        self.category = "State"

    def run(self,state:State):
        return self.func(state=state)

class StateModel(CausalModel):
    def __init__(self,state:State):
        super().__init__()

        self.state = state
        self.var_funcs = state.var_funcs

        for var in self.state.vals:
            node = StateNode(
                name=var,
                vals=self.state.ranges[var],
                func=self.var_funcs[var],
                value=self.state.vals[var]
            )
            self.add_node(node)

    '''
    CAUSAL OPERATIONS
    '''
    def set_value(self, node, new_value):
        super().set_value(node, new_value)
        self.state.set_value(node,new_value)

    def propagate_interventions(self,order:list[str]) -> None:
        for node in order:
            new_val = self.nodes[node].run(self.state)
            self.set_value(node,new_val)



