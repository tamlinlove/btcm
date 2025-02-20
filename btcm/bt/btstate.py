import py_trees
import networkx as nx
import json
import importlib

from typing import Dict

from btcm.dm.state import State

class BTState(State):
    def __init__(self, data: dict, behaviour_dict: Dict[str,py_trees.behaviour.Behaviour]):
        
        self.data = data
        self.behaviour_dict = behaviour_dict

        # Calculate list of variables
        self.calculate_state_attributes()

    '''
    RECONSTRUCT STATE
    '''
    def vars(self):
        pass
    
    def calculate_state_attributes(self):
        vars = []
        for node in self.behaviour_dict:
            # Add return status
            vars.append(f"return_{node}")
            # Add executed variable
            vars.append(f"executed_{node}")

            if self.data["tree"][node]["category"] == "Action":
                # Add decision variable
                vars.append(f"decision_{node}")

        # State
        module = importlib.import_module(self.data["state"]["module"])
        cls = getattr(module, self.data["state"]["class"])
        state_vars = list(cls.ranges().keys())
        vars += state_vars

        print(vars)
    

        return vars

        

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

        


