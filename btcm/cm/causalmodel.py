import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
import copy

from btcm.dm.state import State

from collections.abc import Callable
from typing import List,Dict,Self

def build_state_model(state:State, edges:list[tuple[str,str]]=None):
    '''
    This function builds a CausalModel to model the input State
    '''
    cm = CausalModel(state=state)

    for var in cm.state.vals:
        node = CausalNode(
            name=var,
            vals=cm.state.ranges[var],
            func=cm.state.var_funcs[var],
            value=cm.state.get_value(var),
            category="State"
        )
        cm.add_node(node)

    if edges is not None:
        cm.add_edges(edges)

    return cm

class CausalNode:
    def __init__(self,name:str,vals:list,value,func:Callable,category:str="State"):
        self.name = name
        self.vals = vals
        self.func = func
        self.value = value
        self.category = category

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
            if not (edge in self.graph.edges):
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
    
    def propagation_order(self,nodes:list[str],graph:nx.DiGraph) -> list[str]:
        # Get order for propagation, ignoring nodes that do not descend from intervened nodes
        order = nx.topological_sort(graph)
        reduced_order = []
        for node in order:
            ancestors = nx.ancestors(graph,node)
            for inode in nodes:
                if inode in ancestors:
                    reduced_order.append(node)
                    break
        return reduced_order
    
    def propagate_interventions(self,order:list[str],state:State) -> None:
        for node in order:
            new_val = state.run(node)
            state.set_value(node,new_val)

    def intervene(self,interventions:dict,search_graph:nx.DiGraph) -> tuple[nx.DiGraph,State]:
        # Validate
        for node in interventions:
            if node not in self.nodes:
                raise ValueError(f"Unrecognised node {node}")
            
            if interventions[node] not in self.nodes[node].vals:
                raise ValueError(f"Invalid value {interventions[node]} for node {node}")
        
        # Copy
        new_graph = nx.DiGraph(search_graph)
        new_state = self.state.copy_state(self.state)
        
        for node in interventions:
            # Remove parents
            for parent in self.parents(node):
                # Check if parent has already been removed e.g. for variables that are not allowed to be intervened on
                if parent in new_graph.nodes:
                    new_graph.remove_edge(parent,node)

            # Set new values
            new_state.set_value(node,interventions[node])

        # Propagate changes throughout model
        order = self.propagation_order(list(interventions.keys()),new_graph)
        self.propagate_interventions(order,new_state)

        return new_graph,new_state


    '''
    VISUALISE
    '''
    def visualise(self,graph:nx.DiGraph=None,state:State=None,nodes:dict=None,node_names:Dict[str,str]=None,label_dict:dict=None,colours=None):
        if graph is None:
            graph = self.graph
        if state is None:
            state = self.state

        if nodes is None:
            nodes = self.nodes
        else:
            # Replace graph with only nodes from nodes
            graph = copy.deepcopy(graph)
            graph.remove_nodes_from(graph.nodes()-list(nodes.keys()))
        
        if label_dict is None:
            if node_names is None:
                label_dict = {nodes[node].name: f"{nodes[node].name} = {state.get_value(nodes[node].name)}" for node in nodes}
            else:
                label_dict = {nodes[node].name: f"{node_names[node]} = {state.get_value(nodes[node].name)}" for node in nodes} 

        pos = graphviz_layout(graph, prog="dot")
        nx.draw_networkx_nodes(graph, pos, node_size = 500, node_color=colours)
        nx.draw_networkx_labels(graph, pos, labels=label_dict)
        nx.draw_networkx_edges(graph, pos, edgelist= graph.edges, arrows=True)
        plt.show()

 