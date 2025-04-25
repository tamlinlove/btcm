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
            behaviours_to_node: Dict[py_trees.behaviour.Behaviour,str],
            root:py_trees.behaviour.Behaviour,
    ):  
        self.data = data
        self.behaviour_dict = behaviour_dict
        self.behaviours_to_node = behaviours_to_node
        self.root_node = root

    @classmethod
    def from_data(
            cls,
            data: dict, 
            behaviour_dict: Dict[str,py_trees.behaviour.Behaviour],
            behaviours_to_node: Dict[py_trees.behaviour.Behaviour,str],
            root:py_trees.behaviour.Behaviour,
    ) -> Self:
        obj = cls(data,behaviour_dict,behaviours_to_node,root)
        obj.calculate_state_attributes()
        return obj

    @classmethod
    def copy_state(cls,state:Self) -> Self:
        obj = cls(state.data,state.behaviour_dict,state.behaviours_to_node,state.root_node)
        obj.vars_list = state.vars_list
        obj.range_dict = state.range_dict
        obj.func_dict = state.func_dict
        obj.categories = state.categories
        obj.nodes = state.nodes
        obj.vals = copy.deepcopy(state.vals)
        obj.sub_vars = state.sub_vars
        obj.node_names = state.node_names
        obj.state_class = state.state_class
        obj.dummy_state = state.state_class()
        obj.node_to_inputs = state.node_to_inputs

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
    
    def internal(self, var):
        if self.categories[var] == "State":
            # Can delegate to the state class
            return self.dummy_state.internal(self.node_names[var])
        return False

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
        self.node_names = {}
        self.sub_vars = {node:{} for node in self.behaviour_dict}
        self.node_to_inputs = None

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
            self.node_names[vname] = vname

            # Add executed variable
            vname = f"executed_{node}"
            self.vars_list.append(vname)
            self.range_dict[vname] = self.get_executed_range()
            self.func_dict[vname] = None # TODO: needed?
            self.categories[vname] = "Executed"
            self.sub_vars[node]["Executed"] = vname
            self.nodes[vname] = node
            self.vals[vname] = None
            self.node_names[vname] = vname

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
                self.node_names[vname] = vname

        # State variables
        module = importlib.import_module(self.data["state"]["module"])
        self.state_class = getattr(module, self.data["state"]["class"])
        self.dummy_state = self.state_class()

    def discretise_range(self,var_range:VarRange,num_steps:int=10):
        if var_range.values is not None:
            # Already discrete
            return var_range
        else:
            # Continuous, needs to be discretised
            if var_range.range_type == "cont" and var_range.var_type == float:
                # Can create a discretised float range
                step_size = (var_range.max-var_range.min)/num_steps
                discrete_range = VarRange.discretised_float_range(var_range.min,var_range.max,step_size)
                return discrete_range
            elif var_range.range_type == "any":
                # Cannot be discretised, return as is and hope it is not intervened on
                return var_range
            else:
                raise TypeError(f"Unrecognised var range type: {var_range.range_type}")


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
    VALUES
    '''
    def set_value(self,var:str,value):
        # TODO: Redo for state variables based on tick/time
        # Set own value
        super().set_value(var,value)
        '''
        # Set var_state
        if self.var_state.vals is not None and var in self.var_state.vars():
            self.var_state.set_value(var,value)
        '''
   
    '''
    RUN FUNCTIONS FOR INTERVENTIONS
    '''
    def run(self,node:str):
        if self.categories[node] == "Executed":
            return self.run_executed(node)
        
        # If here, then we need to create a var_state
        var_state = self.state_class()
        var_state.vals = {}
        node_name = self.nodes[node]

        if node_name in self.node_to_inputs:
            node_input = self.node_to_inputs[node_name]
            
            for var in node_input:
                if self.categories[var] == "State":
                    print(var,self.get_value(var))
                    var_state.set_value(self.node_names[var],self.get_value(var))

            if self.categories[node] == "Return":
                return self.run_return(node,var_state)
            if self.categories[node] == "Decision":
                return self.run_decision(node,var_state)
            
            if self.categories[node] == "State":
                all_state = all([self.categories[var] == "State" for var in node_input])
                if all_state:
                    # Can delegate to var_state
                    return var_state.run(self.node_names[node],var_state)
                else:
                    return self.run_internal_state(node,var_state)
            
            # If here, woops
            raise TypeError(f"Unrecognised category {self.categories[node]} for node {node}")
        
    def run_internal_state(self,node:str,var_state:State):
        node_input = self.node_to_inputs[node]
        # Remove node from it's input list
        node_input.remove(node)
        
        # Should be left with a single execution node, a decision node, and optionally a bunch of state vars
        executed = None
        executed_var = None
        decision = None
        self_val = None
        for var in node_input:
            if self.categories[var] == "Executed":
                executed = self.get_value(var)
                executed_var = var
            elif self.categories[var] == "Decision":
                decision = self.get_value(var)
            elif self.categories[var] == "State":
                if self.node_names[var] == self.node_names[node]:
                    self_val = self.get_value(var)

        if executed is None or decision is None:
            raise ValueError(f"Node {node} needs both an executed and decision variable!")

        if executed:
            # Run the node's execute function to determine the new value
            behaviour_node = self.nodes[executed_var]
            behaviour = self.behaviour_dict[behaviour_node]
            # TODO: Get the input variables for the behaviour and add them to the var_state
            for var in self.node_to_inputs[behaviour_node]:
                if self.categories[var] == "State":
                    if not self.node_names[var] in var_state.vals:
                        var_state.set_value(self.node_names[var],self.get_value(var))

            # Execute the behaviour
            behaviour.execute(var_state,decision)

            # Extract the new value
            return var_state.get_value(self.node_names[node])
        else:
            # The node never executed, the value should remain identical
            return self_val
        
    def run_return(self,node:str,var_state:State):
        # TODO: Make sure correct var state is used
        executed_node = self.sub_vars[self.nodes[node]]["Executed"]
        if not self.vals[executed_node]:
            # Node was not executed, always return invalid
            return py_trees.common.Status.INVALID

        node_cat = self.data["tree"][self.nodes[node]]["category"]
        behaviour = self.behaviour_dict[self.nodes[node]]
        if node_cat == "Action":
            corresponding_decision = self.sub_vars[self.nodes[node]]["Decision"]
            action = self.vals[corresponding_decision]
            return behaviour.execute(var_state,action)
        elif node_cat == "Condition":
            action = NullAction()
            return behaviour.execute(var_state,action)
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
        
    def run_decision(self,node:str,var_state:State):
        # TODO: Make sure correct var state is used
        executed_node = self.sub_vars[self.nodes[node]]["Executed"]
        if not self.vals[executed_node]:
            # Node was not executed, always return null action
            return NullAction()

        behaviour:Leaf = self.behaviour_dict[self.nodes[node]]
        return behaviour.decide(var_state)
    
    '''
    INTERVENTIONS
    '''
    def can_intervene(self, node):
        if self.categories[node] == "State":
            return self.dummy_state.can_intervene(self.node_names[node])
        return True

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
        self.state = BTState.from_data(self.data,self.behaviours,self.behaviours_to_nodes,self.tree.root)

        # Create causal model
        self.model,self.state_batches = self.create_causal_model(causal_edges)

        # Get node names
        self.node_names = self.get_node_name_dict()

        # Register blackboard
        self.board = self.register_blackboard(data=self.data,state=self.state,env=dummy_env)


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
        # Register other experiment parameters
        board.register_key("display", access=py_trees.common.Access.WRITE)
        board.set("display", False) # No output for explanations

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
        for var in self.state.vars():
            if self.state.categories[var] == "State":
                node_names[var] = var
        return node_names
    
    def get_leaf_behaviours(self,root):
            leaf_behaviours = []

            def traverse(node):
                if not node.children:
                    # If the node has no children, it is a leaf behaviour
                    leaf_behaviours.append(node)
                else:
                    # Recursively traverse each child
                    for child in node.children:
                        traverse(child)

            # Start traversal from the root node
            traverse(root)

            return leaf_behaviours
    
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
        last_state_time = (0,0)
        self.node_to_inputs = {}

        dummy_state = self.state.state_class()

        node_updates = {}
        while str(curr_tick) in self.data and not found_time:
            data_tick = self.data[str(curr_tick)]
            #curr_time = 0
            while str(curr_time) in data_tick and not found_time:
                # Make Update
                if "update" in data_tick[str(curr_time)]:
                    update = data_tick[str(curr_time)]["update"]
                    for node in update:
                        # Update the values of the BT node variables
                        if "status" in update[node]:
                            self.state.set_value(self.state.sub_vars[node]["Return"],self.status_map[update[node]["status"]])
                        if "action" in update[node] and self.data["tree"][node]["category"] == "Action":
                            action = dummy_state.retrieve_action(update[node]["action"])
                            self.state.set_value(self.state.sub_vars[node]["Decision"],action)

                        node_updates[node] = update[node]["status"]!="Status.INVALID"

                        self.node_to_inputs[node] = []
                        # TODO: Somehow link each var_i to a tick/time for explanation
                        if self.data["tree"][node]["category"] in ["Action","Condition"]:
                            # Update the states of input variables and their ancestors
                            parents = self.model.parents(self.state.sub_vars[node]["Return"])
                            parent_state_vars = [parent for parent in parents if self.state.categories[parent] == "State"]
                            for parent in parent_state_vars:
                                ancestors = list(nx.ancestors(self.model.graph, parent))
                                state_ancestors = [anc for anc in ancestors if self.state.categories[anc] == "State"]
                                same_batch_ancestors = [anc for anc in state_ancestors if self.state_batches[anc] == self.state_batches[parent]]
                                vars_to_update = [parent] + same_batch_ancestors
                                self.node_to_inputs[node] += vars_to_update
                                for var in vars_to_update:
                                    data_tick_time = self.data[str(last_state_time[0])][str(last_state_time[1])] # Use t-1
                                    self.state.set_value(var,data_tick_time["state"][self.state.node_names[var]])

                            self.node_to_inputs[node] = list(set(self.node_to_inputs[node]))

                            # Update the states of output variables
                            children = [var for var in self.model.nodes if self.state.sub_vars[node]["Executed"] in self.model.parents(var)]
                            children_state_vars = [child for child in children if self.state.categories[child] == "State"]
                            for child in children_state_vars:
                                data_tick_time = self.data[str(curr_tick)][str(curr_time)] # Use t
                                self.state.set_value(child,data_tick_time["state"][self.state.node_names[child]])

                #Check if time has been found
                if curr_tick == tick and curr_time == time:
                    found_time = True
                
                last_state_time = (curr_tick,curr_time)
                
                curr_time += 1
            curr_tick += 1

        # Executed nodes
        for node in node_updates:
            self.state.set_value(self.state.sub_vars[node]["Executed"],node_updates[node])
        
        # Correct node executions
        executed_leaves = [node for node in node_updates if node_updates[node]]
        for node in executed_leaves:
            self.update_parent_executions(node)

        # Add parents to state vars in the node to inputs dict
        for var in self.state.vars():
            if self.state.categories[var] == "State":
                self.node_to_inputs[var] = self.model.parents(var) + [var]

        # Inject node to inputs dict to the BTstate
        self.state.node_to_inputs = self.node_to_inputs
        
    def update_parent_executions(self,node):
        # Update node
        self.state.set_value(self.state.sub_vars[node]["Executed"],True)
        # Update parent
        parent = self.behaviours[node].parent
        if parent is not None:
            self.update_parent_executions(self.behaviours_to_nodes[parent])


    def set_initial_state(self):
        data0 = self.data["0"]["0"]

        # Set State Variables
        for state_var in data0["state"]:
            self.state.set_value(f"{state_var}_0",data0["state"][state_var])
        
        # Set behaviour tree node values
        for node in self.state.sub_vars:
            self.state.set_value(self.state.sub_vars[node]["Return"],py_trees.common.Status.INVALID)
            self.state.set_value(self.state.sub_vars[node]["Executed"],False)
            if "Decision" in self.state.sub_vars[node]:
                self.state.set_value(self.state.sub_vars[node]["Decision"],NullAction())

    
    '''
    CAUSAL MODEL
    '''
    def create_state_graph(self,causal_edges:list[tuple[str,str]] = None):
        dummy_state = self.state.state_class()
        if causal_edges is None:
            causal_edges = dummy_state.cm_edges()

        state_graph = nx.DiGraph()
        state_graph.add_edges_from(causal_edges)

        return state_graph
    
    def create_state_variable(self,variable_name:str,variable_counts:dict[str,int],dummy_state:State):
            vname = f"{variable_name}_{variable_counts[variable_name]}"
            self.state.vars_list.append(vname)
            self.state.range_dict[vname] = self.state.discretise_range(dummy_state.ranges()[variable_name])
            self.state.func_dict[vname] = dummy_state.var_funcs()[variable_name]
            self.state.categories[vname] = "State"
            self.state.nodes[vname] = vname
            self.state.vals[vname] = None
            self.state.node_names[vname] = variable_name

    def create_causal_model(self,causal_edges:list[tuple[str,str]] = None) -> CausalModel:
        # Create a graph just for the state, to be used in reconstructing the state later on
        state_graph = self.create_state_graph(causal_edges)

        # First, create a causal model using only the BT node variables
        cm = CausalModel(self.state)
        for var in self.state.vars():
            node = CausalNode(
                    name=var,
                    vals=self.state.ranges()[var].values,
                    func=self.state.var_funcs()[var],
                    category=self.state.categories[var],
                    value=None
                )
            cm.add_node(node)

        # Now, create edges in the graph based on relationships in the BT structure
        for node in self.state.sub_vars:
            if self.data["tree"][node]["category"] in ["Action","Condition"]:
                # Connect Execution and State to Return for leaf nodes
                cm.add_edge((self.state.sub_vars[node]["Executed"],self.state.sub_vars[node]["Return"]))

                if self.data["tree"][node]["category"] == "Action":
                    # Connect Execution and State to Decision for Action nodes
                    cm.add_edge((self.state.sub_vars[node]["Executed"],self.state.sub_vars[node]["Decision"]))
                    # Connect Decision to Return for Action nodes
                    cm.add_edge((self.state.sub_vars[node]["Decision"],self.state.sub_vars[node]["Return"]))
            else:
                # Connect Execution and Return for composite nodes
                cm.add_edge((self.state.sub_vars[node]["Executed"],self.state.sub_vars[node]["Return"]))

                if self.data["tree"][node]["category"] in ["Sequence","Fallback"]:
                    # Composite node, link result to results of all children
                    for child_behaviour in self.behaviours[node].children:
                        child_node = self.behaviours_to_nodes[child_behaviour]
                        cm.add_edge((self.state.sub_vars[child_node]["Return"],self.state.sub_vars[node]["Return"]))
            
            # For all types of nodes, connect execution to parents
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
                
        # Now, create state variables representing every time the variable is potentially modified
        dummy_state = self.state.state_class()
        state_vars = list(dummy_state.ranges().keys())
        var_counts = {var:0 for var in state_vars}
        state_batches = {}
        batch_num = 0

        # Start by creating an initial node for every state variable
        for var in state_vars:
            self.create_state_variable(var,var_counts,dummy_state)

            # Add to cm
            vname = f"{var}_{var_counts[var]}"
            if vname not in cm.nodes:
                var_node = CausalNode(
                    name=vname,
                    vals=self.state.discretise_range(dummy_state.ranges()[var]).values,
                    func=dummy_state.var_funcs()[var],
                    category="State",
                    value=None
                )
                cm.add_node(var_node)

            state_batches[vname] = batch_num

        # Go through every leaf node and link with state vars
        leaves = self.get_leaf_behaviours(self.tree.root)
        for leaf in leaves:
            # Add input variables everywhere they appear
            node_input = leaf.input_variables()
            node = self.behaviours_to_nodes[leaf]
            
            batch_num += 1
            to_increment = {var:False for var in var_counts}
            for input_var in node_input:
                # Create var
                vname = f"{input_var}_{var_counts[input_var]}"

                if vname not in self.state.vars():
                    self.create_state_variable(input_var,var_counts,dummy_state)

                # Add to cm
                if vname not in cm.nodes:
                    var_node = CausalNode(
                        name=vname,
                        vals=self.state.discretise_range(dummy_state.ranges()[input_var]).values,
                        func=dummy_state.var_funcs()[input_var],
                        category="State",
                        value=None
                    )
                    cm.add_node(var_node)
                    state_batches[vname] = batch_num

                # Add ancestors based on causal edges
                ancestors = list(nx.ancestors(state_graph, input_var)) if input_var in state_graph.nodes else []
                for anc in ancestors:
                    anc_name = f"{anc}_{var_counts[anc]}"

                    if anc_name not in self.state.vars():
                        self.create_state_variable(anc,var_counts,dummy_state)
                    
                    if anc_name not in cm.nodes:
                        var_node = CausalNode(
                            name=anc_name,
                            vals=self.state.discretise_range(dummy_state.ranges()[anc]).values,
                            func=dummy_state.var_funcs()[anc],
                            category="State",
                            value=None
                        )
                        cm.add_node(var_node)
                        state_batches[anc_name] = batch_num

                # Link ancestors
                allowed_nodes = ancestors + [input_var]
                for edge in state_graph.edges:
                    if edge[0] in allowed_nodes and edge[1] in allowed_nodes:
                        e0_name = f"{edge[0]}_{var_counts[edge[0]]}"
                        e1_name = f"{edge[1]}_{var_counts[edge[1]]}"
                        cm.add_edge((e0_name,e1_name))

                # Add input edges
                cm.add_edge((vname,self.state.sub_vars[node]["Return"]))
                if self.data["tree"][node]["category"] == "Action":
                    cm.add_edge((vname,self.state.sub_vars[node]["Decision"]))

                # Mark for incrementing
                to_increment[input_var] = True
            
            # Increment
            input_vars = [var for var in to_increment if to_increment[var]]
            vars_to_increment = []
            for ivar in input_vars:
                vars_to_increment.append(ivar)
                ancestors = list(nx.ancestors(state_graph, ivar)) if ivar in state_graph.nodes else []
                vars_to_increment += ancestors
            vars_to_increment = list(set(vars_to_increment))
            for var in vars_to_increment:
                var_counts[var] += 1

            # Add output links
            node_output = leaf.output_variables()

            for output_var in node_output:
                # Create var
                vname = f"{output_var}_{var_counts[output_var]}"
                if vname not in self.state.vars():
                    self.create_state_variable(output_var,var_counts,dummy_state)

                # Add to cm
                if vname not in cm.nodes:
                    var_node = CausalNode(
                        name=vname,
                        vals=self.state.discretise_range(dummy_state.ranges()[output_var]).values,
                        func=dummy_state.var_funcs()[output_var],
                        category="State",
                        value=None
                    )
                    cm.add_node(var_node)

                    state_batches[vname] = batch_num + 1

                cm.add_edge((self.state.sub_vars[node]["Executed"],vname))
                if self.data["tree"][node]["category"] == "Action":
                    cm.add_edge((self.state.sub_vars[node]["Decision"],vname))

        # Link all top-level state variables to themselves temporally
        for var in state_vars:
            top_level = False
            if var in state_graph.nodes:
                parents = list(state_graph.predecessors(var))
                if len(parents) == 0:
                    top_level = True
            else:
                top_level = True

            if top_level:
                for i in range(var_counts[var]-1):
                    e0 = f"{var}_{i}"
                    e1 = f"{var}_{i+1}"
                    cm.add_edge((e0,e1))

        return cm,state_batches
    
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

    def visualise(self,show_values:bool=False,graph:nx.DiGraph=None,state:State=None,only_state_vars:bool=False):
        # Labels
        label_dict = {}
        colour_map = []

        if graph is None:
            graph = self.model.graph

        if state is None:
            state = self.state

        if only_state_vars:
            new_graph = copy.deepcopy(graph)
            for node in graph.nodes:
                if state.categories[node] != "State":
                    new_graph.remove_node(node)
            graph = new_graph

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


        


        


