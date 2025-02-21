import py_trees
import networkx as nx
import json
import importlib

from typing import Dict
from collections.abc import Callable

from btcm.dm.state import State

class BTState(State):
    def __init__(self, data: dict, behaviour_dict: Dict[str,py_trees.behaviour.Behaviour]):
        
        self.data = data
        self.behaviour_dict = behaviour_dict

        # Calculate list of variables
        self.calculate_state_attributes()

    '''
    DEFINING FUNCTIONS
    '''
    def vars(self) -> list[str]:
        return self.vars_list
    
    def ranges(self) -> dict:
        pass

    def var_funcs(self) -> dict:
        pass

    '''
    RECONSTRUCT STATE
    '''
    
    def calculate_state_attributes(self):
        self.vars_list = []
        self.range_dict = {}
        self.func_dict = {}

        for node in self.behaviour_dict:
            # Return Status
            vname = f"return_{node}"
            self.vars_list.append(vname)
            self.range_dict[vname] = self.get_return_range(node)
            self.func_dict[vname] = self.get_return_func(node)

            # Add executed variable
            vname = f"executed_{node}"
            self.vars_list.append(vname)
            self.range_dict[vname] = self.get_executed_range()
            self.func_dict[vname] = self.get_executed_func(node)

            if self.data["tree"][node]["category"] == "Action":
                # Add decision variable
                vname = f"decision_{node}"
                self.vars_list.append(vname)
                self.range_dict[vname] = self.get_decision_range(node)
                self.func_dict[vname] = self.get_decision_func(node)

        # State
        module = importlib.import_module(self.data["state"]["module"])
        cls = getattr(module, self.data["state"]["class"])
        self.var_state = cls()
        state_vars = list(self.var_state.ranges().keys())
        self.vars_list += state_vars
        for var in state_vars:
            self.range_dict[var] = self.var_state.ranges()[var]
            self.func_dict[var] = self.var_state.var_funcs()[var]


    '''
    NODE RANGES
    '''
    def get_return_range(self,node:str) -> list:
        if self.data["tree"][node]["category"] == "Condition":
            # No running
            return [
                py_trees.common.Status.SUCCESS,
                py_trees.common.Status.FAILURE,
                py_trees.common.Status.INVALID,
            ]
        return [
            py_trees.common.Status.RUNNING,
            py_trees.common.Status.SUCCESS,
            py_trees.common.Status.FAILURE,
            py_trees.common.Status.INVALID,
        ]
    
    def get_executed_range(self) -> list[bool]:
        return [False,True]
    
    def get_decision_range(self,node:str) -> list:
        # TODO
        return []

    '''
    NODE FUNCTIONS
    '''
    def get_return_func(self,node:str) -> Callable:
        # TODO: handle both leaf and composite cases
        return None

    def get_executed_func(self,node:str) -> Callable:
        # TODO: handle both leaf and composite cases
        return None
    
    def get_decision_func(self,node:str) -> Callable:
        # TODO: handle both leaf and composite cases
        return None
        

class BTStateManager:
    def __init__(self,filename:str):
        # Read Data
        self.read_from_file(filename)

        # Reconstruct BT
        self.behaviours = {} # Stores mapping from node id string to behaviour object
        self.tree = self.reconstruct_bt()

        # TODO
        BTState(self.data,self.behaviours)


    def read_from_file(self,filename:str):
        with open(filename, 'r') as file:
            self.data = json.load(file)

    def reconstruct_bt(self):
        # Start by recovering the tree graph
        graph = nx.DiGraph()
        tree_dict = self.data["tree"]
        edges = []
        for node in tree_dict:
            graph.add_node(node)
            if "children" in tree_dict[node]:
                for child in tree_dict[node]["children"]:
                    edges.append((node,child))
        graph.add_edges_from(edges)

        # Instantiate the tree
        root = self.instantiate_node(list(nx.topological_sort(graph))[0])
        tree = py_trees.trees.BehaviourTree(root=root)
        return tree

    def instantiate_node(self,node:str) -> py_trees.behaviour.Behaviour:
        node_info = self.data["tree"][node]

        if node_info["category"] == "Sequence":
            behaviour = py_trees.composites.Sequence(
                name = node_info["name"],
                memory=False,
                children=[self.instantiate_node(child) for child in node_info["children"]]
            )
        elif node_info["category"] in ["Action","Condition"]:
            module = importlib.import_module(node_info["module"])
            cls = getattr(module, node_info["class"])
            behaviour = cls()
        else:
            raise ValueError(f"Unknown node category {node_info["category"]}")
        
        self.behaviours[node] = behaviour
        return behaviour

        


