import numpy as np
import networkx as nx
from typing import Self,Dict

# For visualisation
import matplotlib.pyplot as plt

from btcm.dm.state import State,VarRange

class RandomState(State):
    def __init__(
            self,
            num_vars:int,
            connectivity:float,
            top_ratio:float=0.5,
            seed:int=None,
    ):
        # Initialise parameters
        self.num_vars = num_vars
        self.connectivity = connectivity
        self.top_ratio = top_ratio
        self.seed = seed

        # Seed
        if seed is not None:
            np.random.seed(seed)


        # Create variables
        self.var_list,self.num_tops,self.num_bottoms = self.random_vars()

        # Create ground truth causal edges
        self.causal_edges = self.random_causal_edges()
        self.state_graph = nx.DiGraph()
        self.state_graph.add_nodes_from(self.var_list)
        self.state_graph.add_edges_from(self.causal_edges)

        # Initialise state dictionaries
        self.range_dict = self.random_range_dict()
        self.var_funcs_dict = self.random_var_funcs()

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
        num_bottoms = self.num_vars - num_tops

        var_list = []
        for i in range(num_tops):
            var_list.append(f"T{i+1}")

        for i in range(num_bottoms):
            var_list.append(f"B{i+1}")

        return var_list,num_tops,num_bottoms
    
    def random_causal_edges(self) -> list[tuple[str,str]]:
        max_num_edges_total = self.num_vars * (self.num_vars - 1) / 2 # Max number of edges in a DAG
        max_non_top_edges = int(max_num_edges_total - (self.num_tops * (self.num_tops - 1) / 2)) # Max number of edges excluding TOP nodes
        num_edges = int(round(self.connectivity * max_non_top_edges))

        possible_edges = []
        for i in range(self.num_bottoms):
            var_index = self.num_tops + i
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
        func_dict = {
            key: (lambda key: lambda state: state.get_value(key))(key)
            for key in self.var_list
        }

        for var in self.var_list:
            var_parents = list(self.state_graph.predecessors(var))
            if len(var_parents) > 0:
                # Create a function that returns the value of the variable based on its parents
                # TODO
            
    
    '''
    Variable Info
    '''
    def get_range_dict(self) -> Dict[str,VarRange]:
        return self.range_dict
    
    def var_funcs(self) -> dict:
        return self.var_funcs_dict


    
