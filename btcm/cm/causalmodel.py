import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
import copy

from btcm.dm.state import State

from collections.abc import Callable
from typing import List,Dict,Self

class CausalNode:
    def __init__(self,name:str,vals:list,value,func:Callable):
        """
        Initialize a CausalNode instance.

        Parameters:
        - name (str): The name of the node variable. This serves as an identifier for the node.
        - vals (list): A list of possible values that the node can take. These represent the domain of the node variable.
        - value: The real value of the node. This is the actual value assigned to the node.
        - func (Callable): A function that encodes how the value of the node is calculated. Assumes arguments are given the same name as variables.
        """
        self.name = name
        self.vals = vals
        self.func = func
        self.value = value

    def run(self,state:State):
        return self.func(state=state)

class CausalModel:
    def __init__(self,state:State):
        self.nodes:Dict[str,CausalNode] = {}
        self.graph = nx.DiGraph()
        self.state = state

    '''
    GRAPH OPERATIONS
    '''

    def add_node(self,node:CausalNode):
        self.nodes[node.name] = node
        self.graph.add_node(node.name)

    def add_nodes(self,nodes:List[CausalNode]):
        for node in nodes:
            self.add_node(node)

    def add_edge(self,edge:tuple[str,str]):
        if edge[0] in self.nodes and edge[1] in self.nodes:
            self.graph.add_edge(edge[0],edge[1])
        else:
            raise ValueError("Nodes described by edge must be added to causal model before edge")
        
    def add_edges(self,edges:list[tuple[str,str]]):
        for edge in edges:
            self.add_edge(edge)

    def parents(self,node:str):
        return list(self.graph.predecessors(node))
    
    '''
    CAUSAL OPERATIONS
    '''
    def value_dict(self) -> dict:
        val_dict = {}
        for node in self.nodes:
            val_dict[node] = self.nodes[node].value
        return val_dict
    
    def propagation_order(self,nodes:list[str]) -> list[str]:
        # Get order for propagation, ignoring nodes that do not descend from intervened nodes
        order = nx.topological_sort(self.graph)
        reduced_order = []
        for node in order:
            ancestors = nx.ancestors(self.graph,node)
            for inode in nodes:
                if inode in ancestors:
                    reduced_order.append(node)
                    break
        return reduced_order
    
    def propagate_interventions(self,order:list[str]) -> None:
        for node in order:
            new_val = self.nodes[node].run(self.state)
            self.set_value(node,new_val)

    def set_value(self,node:str,new_value):
        self.nodes[node].value = new_value
        self.state.set_value(node,new_value)

    def intervene(self,nodes:list[str],values:list) -> Self:
        # Validate
        for (node,value) in zip(nodes,values):
            if node not in self.nodes:
                raise ValueError(f"Unrecognised node {node}")
            
            if value not in self.nodes[node].vals:
                raise ValueError(f"Invalid value {value} for node {node}")
        
        # Copy
        new_model = copy.deepcopy(self)
        
        for (node,value) in zip(nodes,values):
            # Remove parents
            for parent in new_model.parents(node):
                new_model.graph.remove_edge(parent,node)

            # Set new values
            new_model.set_value(node,value)

        # Propagate changes throughout model
        order = new_model.propagation_order(nodes)
        new_model.propagate_interventions(order)

        return new_model


    '''
    VISUALISE
    '''
    def visualise(self):
        label_dict = {self.nodes[node].name: f"{self.nodes[node].name} = {self.nodes[node].value}" for node in self.nodes}
        pos = graphviz_layout(self.graph, prog="dot")
        nx.draw_networkx_nodes(self.graph, pos, node_size = 500)
        nx.draw_networkx_labels(self.graph, pos, labels=label_dict)
        nx.draw_networkx_edges(self.graph, pos, edgelist= self.graph.edges, arrows=True)
        plt.show()

 