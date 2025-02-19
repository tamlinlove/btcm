from btcm.cm.causalmodel import CausalModel,CausalNode
from btcm.dm.state import State

class StateNode(CausalNode):
    def __init__(self, name, vals, func, value):
        super().__init__(name=name, vals=vals, func=func, value=value)

        self.category = "State"

class StateModel(CausalModel):
    def __init__(self,state:State):
        super().__init__(state=state)

        for var in self.state.vals:
            node = StateNode(
                name=var,
                vals=self.state.ranges[var],
                func=self.state.var_funcs[var],
                value=self.state.vals[var]
            )
            self.add_node(node)



