import py_trees
import networkx as nx
import json
import importlib
import copy

from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt

from typing import Dict,List,Self
from collections.abc import Callable

from btcm.dm.state import State,VarRange
from btcm.dm.action import NullAction
from btcm.cm.causalmodel import CausalModel,CausalNode
from btcm.bt.nodes import Leaf
from btcm.dm.environment import Environment

'''

TODO: 
Right now, the blackboard and environment are ignored basically by the BTState, Causal Model and Explainer.
This is fine for the moment as uncertainty in state evolution is not considered. But if it is, this will need to change.

'''

class BTState(State):
    def __init__(
            self,
            data: dict,
            behaviour_dict: Dict[str,py_trees.behaviour.Behaviour],
            behaviours_to_node: Dict[py_trees.behaviour.Behaviour,str]
    ):  
        self.data = data
        self.behaviour_dict = behaviour_dict
        self.behaviours_to_node = behaviours_to_node

    @classmethod
    def from_data(
            cls,
            data: dict, 
            behaviour_dict: Dict[str,py_trees.behaviour.Behaviour],
            behaviours_to_node: Dict[py_trees.behaviour.Behaviour,str]
    ) -> Self:
        obj = cls(data,behaviour_dict,behaviours_to_node)
        obj.calculate_state_attributes()
        return obj

    @classmethod
    def copy_state(cls,state:Self) -> Self:
        obj = cls(state.data,state.behaviour_dict,state.behaviours_to_node)
        obj.vars_list = state.vars_list
        obj.range_dict = state.range_dict
        obj.func_dict = state.func_dict
        obj.categories = state.categories
        obj.nodes = state.nodes
        obj.vals = copy.deepcopy(state.vals)
        obj.sub_vars = state.sub_vars
        obj.var_state = state.var_state

        return obj


    '''
    DEFINING FUNCTIONS
    '''
    def vars(self) -> list[str]:
        return self.vars_list
    
    def ranges(self) -> dict:
        return self.range_dict

    def var_funcs(self) -> dict:
        return self.func_dict

    '''
    RECONSTRUCT STATE
    '''
    
    def calculate_state_attributes(self):
        self.vars_list = []
        self.range_dict = {}
        self.func_dict = {}
        self.categories = {}
        self.nodes = {}
        self.vals = {}
        self.sub_vars = {node:{} for node in self.behaviour_dict}

        for node in self.behaviour_dict:
            # Return Status
            vname = f"return_{node}"
            self.vars_list.append(vname)
            self.range_dict[vname] = self.get_return_range(node)
            self.func_dict[vname] = None # TODO: needed?
            self.categories[vname] = "Return"
            self.sub_vars[node]["Return"] = vname
            self.nodes[vname] = node
            self.vals[vname] = None
            self.var_state: State = None

            # Add executed variable
            vname = f"executed_{node}"
            self.vars_list.append(vname)
            self.range_dict[vname] = self.get_executed_range()
            self.func_dict[vname] = None # TODO: needed?
            self.categories[vname] = "Executed"
            self.sub_vars[node]["Executed"] = vname
            self.nodes[vname] = node
            self.vals[vname] = None


            if self.data["tree"][node]["category"] == "Action":
                # Add decision variable
                vname = f"decision_{node}"
                self.vars_list.append(vname)
                self.range_dict[vname] = self.get_decision_range(node)
                self.func_dict[vname] = None # TODO: needed?
                self.categories[vname] = "Decision"
                self.sub_vars[node]["Decision"] = vname
                self.nodes[vname] = node
                self.vals[vname] = None

        # State variables
        module = importlib.import_module(self.data["state"]["module"])
        cls = getattr(module, self.data["state"]["class"])
        self.var_state = cls()
        state_vars = list(self.var_state.ranges().keys())
        self.vars_list += state_vars
        for var in state_vars:
            self.range_dict[var] = self.var_state.ranges()[var]
            self.func_dict[var] = self.var_state.var_funcs()[var]
            self.categories[var] = "State"
            self.nodes[var] = var
            self.vals[var] = None

    '''
    NODE RANGES
    '''
    def get_return_range(self,node:str) -> list:
        if self.data["tree"][node]["category"] == "Condition":
            # No running
            return VarRange.categorical([
                py_trees.common.Status.SUCCESS,
                py_trees.common.Status.FAILURE,
                py_trees.common.Status.INVALID,
            ])
        return VarRange.categorical([
            py_trees.common.Status.RUNNING,
            py_trees.common.Status.SUCCESS,
            py_trees.common.Status.FAILURE,
            py_trees.common.Status.INVALID,
        ])
    
    def get_executed_range(self) -> list[bool]:
        return VarRange.boolean()
    
    def get_decision_range(self,node:str) -> list:
        dec_range = copy.deepcopy(self.behaviour_dict[node].action_space())
        null = NullAction()
        if null not in dec_range:
            dec_range.append(null)
        return VarRange.categorical(dec_range)
    
    '''
    VARIABLE FUNCTIONS
    '''
    @staticmethod
    def sequence_return(child_returns:list,executed:bool):
        '''
        Calculate the return of a sequence node given a list of its children's returns, in order from left to right
        '''
        if not executed:
            return py_trees.common.Status.INVALID
        for child_return in child_returns:
            if child_return in [py_trees.common.Status.FAILURE,py_trees.common.Status.RUNNING]:
                return child_return
            elif child_return == py_trees.common.Status.INVALID:
                # Should not be possible normally, but may occurr during interventions
                return child_return
        # Must have succeeded
        return py_trees.common.Status.SUCCESS
    
    @staticmethod
    def fallback_return(child_returns:list,executed:bool):
        '''
        Calculate the return of a fallback node given a list of its children's returns, in order from left to right
        '''
        if not executed:
            return py_trees.common.Status.INVALID
        for child_return in child_returns:
            if child_return in [py_trees.common.Status.SUCCESS,py_trees.common.Status.RUNNING]:
                return child_return
            elif child_return == py_trees.common.Status.INVALID:
                # Should not be possible normally, but may occurr during interventions
                return child_return
        # Must have failed
        return py_trees.common.Status.FAILURE
    
    '''
    RUN FUNCTIONS FOR INTERVENTIONS
    '''
    def run(self,node:str):
        if self.categories[node] == "State":
            # State node, delegate to var_state
            return self.var_state.run(node,self)
        if self.categories[node] == "Return":
            # Return node, decide which case
            return self.run_return(node)
        if self.categories[node] == "Executed":
            # Executed node, decide which case
            return self.run_executed(node)
        if self.categories[node] == "Decision":
            return self.run_decision(node)
    
        raise ValueError(f"Unrecognised category {self.categories[node]}")
        
    def run_return(self,node:str):
        executed_node = self.sub_vars[self.nodes[node]]["Executed"]
        if not self.vals[executed_node]:
            # Node was not executed, always return invalid
            return py_trees.common.Status.INVALID

        node_cat = self.data["tree"][self.nodes[node]]["category"]
        behaviour = self.behaviour_dict[self.nodes[node]]
        if node_cat == "Action":
            corresponding_decision = self.sub_vars[self.nodes[node]]["Decision"]
            action = self.vals[corresponding_decision]
            return behaviour.execute(self,action)
        elif node_cat == "Condition":
            action = NullAction()
            return behaviour.execute(self,action)
        elif node_cat == "Sequence":
            children  = behaviour.children
            child_nodes = [self.behaviours_to_node[child] for child in children]
            child_return_nodes = [self.sub_vars[child]["Return"] for child in child_nodes]
            child_return_vals = [self.vals[child] for child in child_return_nodes]
            return self.sequence_return(child_return_vals,True)
        elif node_cat == "Fallback":
            children  = behaviour.children
            child_nodes = [self.behaviours_to_node[child] for child in children]
            child_return_nodes = [self.sub_vars[child]["Return"] for child in child_nodes]
            child_return_vals = [self.vals[child] for child in child_return_nodes]
            return self.fallback_return(child_return_vals,True)
        
        # Sholdn't be here
        raise TypeError(f"Unknown node category: {node_cat}")
        
    def run_executed(self,node:str):
        behaviour = self.behaviour_dict[self.nodes[node]]
        if behaviour.parent is None:
            # Root node, always executed
            return True
        
        # Is child of a composite node
        siblings = behaviour.parent.children
        if behaviour == siblings[0]:
            # First child, depends only on parent's execution status
            parent_node = self.behaviours_to_node[behaviour.parent]
            corresponding_execution = self.sub_vars[parent_node]["Executed"]
            return self.vals[corresponding_execution]
        
        # Second child onwards, depends on left sibling
        if isinstance(behaviour.parent,py_trees.composites.Sequence):
            # Sequence parent, runs if left sibling succeeds
            lsib = siblings[siblings.index(behaviour)-1]
            lsib_node = self.behaviours_to_node[lsib]
            corresponding_return = self.sub_vars[lsib_node]["Return"]
            return self.vals[corresponding_return] == py_trees.common.Status.SUCCESS
        elif isinstance(behaviour.parent,py_trees.composites.Selector):
            # Fallback parent, runs if left sibling fails
            lsib = siblings[siblings.index(behaviour)-1]
            lsib_node = self.behaviours_to_node[lsib]
            corresponding_return = self.sub_vars[lsib_node]["Return"]
            return self.vals[corresponding_return] == py_trees.common.Status.FAILURE

        
        # Shouldn't be here
        raise TypeError(f"Unknown parent type: {self.data["tree"][self.behaviours_to_node[behaviour.parent]]["category"]}")
        
    def run_decision(self,node:str):
        executed_node = self.sub_vars[self.nodes[node]]["Executed"]
        if not self.vals[executed_node]:
            # Node was not executed, always return null action
            return NullAction()

        behaviour:Leaf = self.behaviour_dict[self.nodes[node]]
        return behaviour.decide(self)

class BTStateManager:
    status_map = {
        "Status.SUCCESS":py_trees.common.Status.SUCCESS,
        "Status.FAILURE":py_trees.common.Status.FAILURE,
        "Status.RUNNING":py_trees.common.Status.RUNNING,
        "Status.INVALID":py_trees.common.Status.INVALID,
    }

    def __init__(self,filename:str,causal_edges:list[tuple[str,str]] = None,dummy_env:Environment=None,directory=""):
        # Read Data
        self.read_from_file(filename,directory)

        # Reconstruct BT
        self.behaviours = {} # Stores mapping from node id string to behaviour object
        self.behaviours_to_nodes = {} # Stores mapping from behaviour object to node id string
        self.graph,self.tree = self.reconstruct_bt()

        # Create a BT State
        self.state = BTState.from_data(self.data,self.behaviours,self.behaviours_to_nodes)

        # Register blackboard
        self.board = self.register_blackboard(data=self.data,state=self.state,env=dummy_env)

        # Create causal model
        self.model = self.create_causal_model(causal_edges)

        # Get node names
        self.node_names = self.get_node_name_dict()


    def read_from_file(self,filename:str,directory:str):
        if directory == "":
            filepath = filename
        else:
            filepath = f"{directory}/{filename}"
        with open(filepath, 'r') as file:
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
        return graph,tree

    def instantiate_node(self,node:str) -> py_trees.behaviour.Behaviour:
        node_info = self.data["tree"][node]

        if node_info["category"] == "Sequence":
            behaviour = py_trees.composites.Sequence(
                name = node_info["name"],
                memory=node_info["memory"],
                children=[self.instantiate_node(child) for child in node_info["children"]]
            )
        elif node_info["category"] == "Fallback":
            behaviour = py_trees.composites.Selector(
                name = node_info["name"],
                memory=node_info["memory"],
                children=[self.instantiate_node(child) for child in node_info["children"]]
            )
        elif node_info["category"] in ["Action","Condition"]:
            module = importlib.import_module(node_info["module"])
            cls = getattr(module, node_info["class"])
            behaviour = cls()
        else:
            raise ValueError(f"Unknown node category {node_info['category']}")
        
        self.behaviours[node] = behaviour
        self.behaviours_to_nodes[behaviour] = node
        return behaviour
    
    def register_blackboard(self,data:dict,state:State,env:Environment) -> py_trees.blackboard.Client:
        # Create blackboard
        board = py_trees.blackboard.Client(name="Board")
        # Register state
        board.register_key("state", access=py_trees.common.Access.WRITE)
        board.set("state", state) 
        # Register environment
        board.register_key("environment", access=py_trees.common.Access.WRITE)
        if env is not None:
            # Use provided dummy environment
            board.set("environment", env)
        else:
            # Create new environment based on logger data
            module = importlib.import_module(self.data["environment"]["module"])
            cls = getattr(module, self.data["environment"]["class"])
            board.set("environment", cls(board.state)) 

        return board
    
    '''
    UTILITY
    '''
    def get_node_from_name(self,node_name:str,node_type:str):
        # Find the identifier for the node
        matching_nodes = [
            node_id for node_id, node_data in self.data["tree"].items()
            if node_data["name"] == node_name
        ]
        if len(matching_nodes) == 0:
            raise ValueError(f"No node found with name '{node_name}'")
        if len(matching_nodes) > 1:
            raise ValueError(f"Multiple nodes found with name '{node_name}'")
        node_id = matching_nodes[0]

        # Add node type
        if node_type == "Return":
            return f"return_{node_id}"
        elif node_type == "Executed":
            return f"executed_{node_id}"
        elif node_type == "Decision":
            return f"decision_{node_id}"
        else:
            raise ValueError(f"Unknown node type '{node_type}'")
        
    def get_node_name_dict(self):
        # Get node names
        node_names = {}
        for node in self.data["tree"]:
            node_names["return_"+node] = "return_"+self.data["tree"][node]["name"]
            node_names["executed_"+node] = "executed_"+self.data["tree"][node]["name"]
            if self.data["tree"][node]["category"] == "Action":
                node_names["decision_"+node] = "decision_"+self.data["tree"][node]["name"]
        # Add names of state variables
        for var in self.state.var_state.ranges():
            node_names[var] = var
        return node_names
    
    '''
    VALUES
    '''
    def load_state(self,tick:int=0,time="end"):
        if str(tick) not in self.data:
            raise ValueError(f"Timestep {tick}-{time} not in data")

        if time == "end":
            time = sorted(int(key) for key in self.data[str(tick)].keys())[-1]

        if str(time) not in self.data[str(tick)]:
            raise ValueError(f"Timestep {tick}-{time} not in data")

        self.set_initial_state()
        # Iterate through timesteps until current time
        curr_tick = 0
        curr_time = 0
        found_time = False
        state_vals = None


        # TODO: Unclear on how to handle "resets"

        node_updates = {}
        while str(curr_tick) in self.data and not found_time:
            data_tick = self.data[str(curr_tick)]
            #curr_time = 0
            while str(curr_time) in data_tick and not found_time:
                # Make Update
                if "update" in data_tick[str(curr_time)]:
                    update = data_tick[str(curr_time)]["update"]
                    for node in update:
                        if "status" in update[node]:
                            self.state.set_value(self.state.sub_vars[node]["Return"],self.status_map[update[node]["status"]])
                        if "action" in update[node] and self.data["tree"][node]["category"] == "Action":
                            action = self.state.var_state.retrieve_action(update[node]["action"])
                            self.state.set_value(self.state.sub_vars[node]["Decision"],action)
                        node_updates[node] = update[node]["status"]!="Status.INVALID"

                #Check if time has been found
                if curr_tick == tick and curr_time == time:
                    found_time = True
                
                # Update state - NB: for t, use state at t-1
                state_vals = data_tick[str(curr_time)]["state"]
                curr_time += 1
            curr_tick += 1

        # Executed nodes
        for node in node_updates:
            self.state.set_value(self.state.sub_vars[node]["Executed"],node_updates[node])

        # State variables
        for state_var in state_vals:
            self.state.set_value(state_var,state_vals[state_var])

        
            

    def set_initial_state(self):
        data0 = self.data["0"]["0"]
        # Set State Variables
        for state_var in data0["state"]:
            self.state.set_value(state_var,data0["state"][state_var])

        # Set behaviour tree node values
        for node in self.state.sub_vars:
            self.state.set_value(self.state.sub_vars[node]["Return"],py_trees.common.Status.INVALID)
            self.state.set_value(self.state.sub_vars[node]["Executed"],False)
            if "Decision" in self.state.sub_vars[node]:
                self.state.set_value(self.state.sub_vars[node]["Decision"],NullAction())

    
    '''
    CAUSAL MODEL
    '''
    
    def create_causal_model(self,causal_edges:list[tuple[str,str]] = None) -> CausalModel:
        cm = CausalModel(self.state)

        # Create nodes with dummy values
        for var in self.state.vars():
            node = CausalNode(
                name=var,
                vals=self.state.ranges()[var],
                func=self.state.var_funcs()[var],
                category=self.state.categories[var],
                value=None
            )
            cm.add_node(node)

        # Create edges
        for node in self.state.sub_vars:
            if self.data["tree"][node]["category"] in ["Action","Condition"]:
                # Connect Execution and State to Return for leaf nodes
                cm.add_edge((self.state.sub_vars[node]["Executed"],self.state.sub_vars[node]["Return"]))
                # TODO: Handle state variation over time????
                for ivar in self.behaviours[node].input_variables():
                    cm.add_edge((ivar,self.state.sub_vars[node]["Return"]))
                if self.data["tree"][node]["category"] == "Action":
                    # Connect Execution and State to Decision for Action nodes
                    cm.add_edge((self.state.sub_vars[node]["Executed"],self.state.sub_vars[node]["Decision"]))
                    # Connect Decision to Return for Action nodes
                    cm.add_edge((self.state.sub_vars[node]["Decision"],self.state.sub_vars[node]["Return"]))
                    # TODO: Handle state variation over time????
                    for ivar in self.behaviours[node].input_variables():
                        cm.add_edge((ivar,self.state.sub_vars[node]["Decision"]))

                if self.behaviours[node].parent is not None:
                    parent_node = self.behaviours_to_nodes[self.behaviours[node].parent]
                    if self.data["tree"][parent_node]["category"] in ["Sequence","Fallback"]:
                        # COMPOSITE
                        siblings = self.behaviours[node].parent.children
                        if self.behaviours[node] == siblings[0]:
                            # Node is the left child of a composite, link execution to parent execution
                            cm.add_edge((self.state.sub_vars[parent_node]["Executed"],self.state.sub_vars[node]["Executed"]))
                        else:
                            # Node is not a leftmost child, link to return of left child
                            lsib = self.behaviours_to_nodes[siblings[siblings.index(self.behaviours[node])-1]]
                            cm.add_edge((self.state.sub_vars[lsib]["Return"],self.state.sub_vars[node]["Executed"]))
                    else:
                        raise TypeError(f"Unknown node category: {self.data['tree'][parent_node]['category']}")
                
            else:
                # Connect Execution and Return for composite nodes
                cm.add_edge((self.state.sub_vars[node]["Executed"],self.state.sub_vars[node]["Return"]))

                if self.data["tree"][node]["category"] in ["Sequence","Fallback"]:
                    # Composite node, link result to results of all children
                    for child_behaviour in self.behaviours[node].children:
                        child_node = self.behaviours_to_nodes[child_behaviour]
                        cm.add_edge((self.state.sub_vars[child_node]["Return"],self.state.sub_vars[node]["Return"]))

        # Create edges for state variables (intra-state)
        if causal_edges is None:
            # No edges provided, attempt to get from state
            causal_edges = self.state.var_state.cm_edges()

        for edge in causal_edges:
            cm.add_edge(edge)

        return cm
    
    '''
    VISUALISATION
    '''
    def visualise_tree(self):
        # Labels
        label_dict = {}
        colour_map = []

        for node in self.graph.nodes:
            if self.data["tree"][node]["category"] == "Action":
                label_dict[node] = f"{self.data['tree'][node]['name']}"
                colour_map.append("green")
            elif self.data["tree"][node]["category"] == "Condition":
                label_dict[node] = f"{self.data['tree'][node]['name']}"
                colour_map.append("red")
            elif self.data["tree"][node]["category"] == "Sequence":
                label_dict[node] = f"{self.data['tree'][node]['name']}"
                colour_map.append("yellow")
            elif self.data["tree"][node]["category"] == "Fallback":
                label_dict[node] = f"{self.data['tree'][node]['name']}"
                colour_map.append("cyan")
            else:
                raise ValueError(f"Invalid node category: {self.data['tree'][node]['category']}")

        pos = graphviz_layout(self.graph, prog="dot")
        nx.draw_networkx_nodes(self.graph, pos, node_size=500, node_color=colour_map)
        nx.draw_networkx_labels(self.graph, pos, labels=label_dict)
        nx.draw_networkx_edges(self.graph, pos, edgelist=self.graph.edges, arrows=True)
        plt.show()

    def visualise(self,show_values:bool=False,graph:nx.DiGraph=None,state:State=None):
        # Labels
        label_dict = {}
        colour_map = []

        if graph is None:
            graph = self.model.graph
        if state is None:
            state = self.state

        for node in graph.nodes:
            val_statement = ""
            if show_values:
                val_statement = f" = {state.get_value(node)}"

            if state.categories[node] == "State":
                # State
                label_dict[node] = f"{state.nodes[node]}_State{val_statement}"
                colour_map.append("green")
            else:
                # Related to BT node
                nodename = self.behaviours[state.nodes[node]].name
                if state.categories[node] == "Return":
                    label_dict[node] = f"{nodename}_Return{val_statement}"
                    colour_map.append("red")
                elif state.categories[node] == "Executed":
                    label_dict[node] = f"{nodename}_Executed{val_statement}"
                    colour_map.append("yellow")
                elif state.categories[node] == "Decision":
                    label_dict[node] = f"{nodename}_Decision{val_statement}"
                    colour_map.append("cyan")
                else:
                    raise ValueError(f"Invalid node category: {state.categories[node]}")


        pos = graphviz_layout(graph, prog="dot")
        nx.draw_networkx_nodes(graph, pos, node_size = 500, node_color=colour_map)
        nx.draw_networkx_labels(graph, pos, labels=label_dict)
        nx.draw_networkx_edges(graph, pos, edgelist= graph.edges, arrows=True)
        plt.show()


        


        


