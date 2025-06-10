import numpy as np
import networkx as nx
from typing import Self,Dict

# For visualisation
import matplotlib.pyplot as plt

from btcm.dm.state import State,VarRange
from btcm.dm.action import Action,NullAction

class RandomState(State):
    def __init__(
            self,
            num_vars:int,
            connectivity:float,
            top_ratio:float=0.5,
            internal_ratio:float=0.25,
            seed:int=None,
            visualise:bool=False
    ):
        # Initialise parameters
        self.num_vars = num_vars
        self.connectivity = connectivity
        self.top_ratio = top_ratio
        self.internal_ratio = internal_ratio
        self.seed = seed

        # Seed
        if seed is not None:
            np.random.seed(seed)


        # Create variables
        self.var_list,self.tops,self.bottoms,self.internals = self.random_vars()

        # Create ground truth causal edges
        self.causal_edges = self.random_causal_edges()
        self.state_graph = nx.DiGraph()
        self.state_graph.add_nodes_from(self.var_list)
        self.state_graph.add_edges_from(self.causal_edges)

        # Visualise the state graph
        if visualise:
            nx.draw(self.state_graph, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, font_color='black', arrows=True)
            plt.show()

        # Initialise state dictionaries
        self.range_dict = self.random_range_dict()
        self.var_funcs_dict,self.func_seeds = self.random_var_funcs()

        # Initialise state
        self.set_initial_values()

        

    @classmethod
    def copy_state(cls,state:Self) -> Self:
        return cls(num_vars=state.num_vars,
                   connectivity=state.connectivity,
                   top_ratio=state.top_ratio,
                   seed=state.seed)
    
    '''
    Random State Generation
    '''
    def random_vars(self) -> list[str]:
        num_tops = round(self.top_ratio * self.num_vars)
        num_internals = round(self.internal_ratio * self.num_vars)
        num_bottoms = self.num_vars - num_tops - num_internals

        var_list = []
        tops = []
        bottoms = []
        internals = []

        for i in range(num_tops):
            var_list.append(f"T{i+1}")
            tops.append(f"T{i+1}")

        for i in range(num_internals):
            var_list.append(f"I{i+1}")
            internals.append(f"T{i+1}")

        for i in range(num_bottoms):
            var_list.append(f"B{i+1}")
            bottoms.append(f"T{i+1}")

        return var_list,tops,bottoms,internals
    
    def random_causal_edges(self) -> list[tuple[str,str]]:
        max_num_edges_total = self.num_vars * (self.num_vars - 1) / 2 # Max number of edges in a DAG
        num_toppables = len(self.tops) + len(self.internals)
        max_non_top_edges = int(max_num_edges_total - (num_toppables * (num_toppables - 1) / 2)) # Max number of edges excluding TOP and Internal nodes
        num_edges = int(round(self.connectivity * max_non_top_edges))

        possible_edges = []
        for i in range(len(self.bottoms)):
            var_index = len(self.tops) + len(self.internals) + i
            for j in range(var_index):
                possible_edges.append((self.var_list[j], self.var_list[var_index]))

        possible_edge_indices = list(range(len(possible_edges)))

        edge_indices = np.random.choice(
            possible_edge_indices,
            size=num_edges,
            replace=False
        )

        edges = [possible_edges[i] for i in edge_indices]
        return list(edges)


    def random_range_dict(self) -> Dict[str,VarRange]:
        return {var:VarRange.boolean() for var in self.var_list}
    
    def random_var_funcs(self) -> dict:
        # Initialise variable functions as just returning the variable value for all variables
        func_seeds = {}

        func_dict = {
            key: (lambda key: lambda state: state.get_value(key))(key)
            for key in self.var_list
        }

        for var in self.var_list:
            var_parents = list(self.state_graph.predecessors(var))
            func_seeds[var] = np.random.randint(0, 10000)
            if len(var_parents) > 0:
                def child_func(state:Self,var:str=var,var_parents:list[str]=var_parents):
                    rng = np.random.default_rng(state.func_seeds[var])
                    combined_value = state.get_value(var_parents[0])
                    
                    for parent in var_parents[1:]:
                        if rng.choice([True, False]):
                            combined_value = combined_value and state.get_value(parent)
                        else:
                            combined_value = combined_value or state.get_value(parent)
                    return combined_value

                func_dict[var] = child_func

        return func_dict,func_seeds
    
    def set_initial_values(self):
        default = self.default_values()

        self.vals = {}
        for var in self.var_list:
            self.set_value(var, default[var])

        self.propagate_internal_values()


    def propagate_internal_values(self):
        order = nx.topological_sort(self.state_graph)
        for node in order:
            old_value = self.get_value(node)
            new_value = self.run(node,self)
            self.set_value(node, new_value)
            
    
    '''
    Variable Info
    '''
    def get_range_dict(self) -> Dict[str,VarRange]:
        return self.range_dict
    
    def var_funcs(self) -> dict:
        return self.var_funcs_dict
    
    def internal(self,var:str) -> bool:
        return var in self.internals
    
    '''
    Execution
    '''
    def run(self,node:str,state:State):
        return self.var_funcs()[node](state)
    
    '''
    Actions
    '''
    @staticmethod
    def retrieve_action(action_name):
        if action_name.startswith("RandomAction"):
            action_num = int(action_name.replace("RandomAction", ""))
            if action_num < 0 or action_num >= RandomAction.num_vals:
                raise ValueError(f"Action number must be in range 0 to {RandomAction.num_vals - 1}, got {action_num}")
            return RandomAction(action_num)
        elif action_name == "NullAction":
            return NullAction()
        else:
            raise ValueError(f"Unknown action name: {action_name}")
        
    '''
    Values
    '''
    def default_values(self):
        # Should be consistent across all seeds
        rng = np.random.default_rng(42)

        default_vals = {}
        for var in self.var_list:
            default_vals[var] = bool(rng.choice(self.range_dict[var].values))

        return default_vals

               
    '''
    Causal Model
    '''
    def cm_edges(self) -> list[tuple[str,str]]:
        return self.causal_edges
    
    def can_intervene(self, node):
        return True
    
    '''
    Interventions for experiments
    '''
    def flip(self, var:str) -> None:
        
        # Flip the value of the variable
        current_value = self.get_value(var)
        new_value = not current_value
        self.set_value(var, new_value)
        
        # Update the state graph if necessary
        self.propagate_internal_values()
    
    '''
    Semantic Info
    '''
    def semantic_dict(self) -> dict[str,str]:
        return {var:f"{var} is a variable in the random state." for var in self.var_list}
    
    '''
    INFORMATION FOR STATE RECONSTRUCTION
    '''
    def consistent(self):
        return False

        
        
class RandomAction(Action):
    name = "RandomAction"
    num_vals = 4

    def __init__(self,action_num:int):
        super().__init__()

        if action_num in list(range(self.num_vals)):
            self.action_num = action_num
        else:
            raise ValueError(f"Action number must be in range 0 to {self.num_vals - 1}, got {action_num}")
        
        self.name = f"RandomAction{self.action_num}"

    @staticmethod
    def action_combos():
        return [RandomAction(i) for i in range(RandomAction.num_vals)]

    
