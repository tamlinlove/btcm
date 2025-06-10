import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import numpy as np
import py_trees

# For visualisation
import matplotlib.pyplot as plt

from btcm.examples.random.random_state import RandomState,RandomAction
from btcm.dm.action import NullAction
from btcm.bt.nodes import ActionNode,ConditionNode

class RandomActionNode(ActionNode):
    def __init__(self,inputs:list[str],outputs:list[str],actions:list[RandomAction],seed:int=None,name:str = "RandomActionNode"):
        super(RandomActionNode, self).__init__(name)

        self.inputs = inputs
        self.outputs = outputs
        self.actions = actions
        self.seed = seed

    def decide(self, state:RandomState) -> RandomAction:
        if self.inputs == []:
            state_seed = 0
        else:
            state_seed = int(''.join('1' if var else '0' for var in self.inputs), 2)

        seed_seed = self.seed if self.seed is not None else 0
        combined_seed = state_seed + seed_seed

        rng = np.random.default_rng(combined_seed)

        return rng.choice(self.actions)
    
    def execute(self, state:RandomState, action:RandomAction) -> py_trees.common.Status:
        if self.inputs == []:
            state_seed = 0
        else:
            state_seed = int(''.join('1' if var else '0' for var in self.inputs), 2)
        action_seed = int(action.name.replace("RandomAction", ""))
        seed_seed = self.seed if self.seed is not None else 0
        combined_seed = state_seed + action_seed + seed_seed

        rng = np.random.default_rng(combined_seed)

        # For this formulation, we ignore Running status
        return rng.choice([py_trees.common.Status.SUCCESS, py_trees.common.Status.FAILURE])
    
    def input_variables(self):
        return self.inputs
    
    def output_variables(self):
        return self.outputs
    
    def action_space(self):
        return self.actions + [NullAction()]
    
    def semantic_description(self) -> str:
        return "Random action node"
    
class RandomConditionNode(ConditionNode):
    def __init__(self,inputs:list[str],seed:int=None,name:str="RandomConditionNode"):
        super(RandomConditionNode, self).__init__(name)

        self.inputs = inputs
        self.seed = seed

    def execute(self, state, _):
        state_seed = int(''.join('1' if var else '0' for var in self.inputs), 2)
        seed_seed = self.seed if self.seed is not None else 0
        combined_seed = state_seed + seed_seed

        rng = np.random.default_rng(combined_seed)

        # For this formulation, we ignore Running status
        return rng.choice([py_trees.common.Status.SUCCESS, py_trees.common.Status.FAILURE])
    
    def input_variables(self):
        return self.inputs
    
    def output_variables(self):
        return []
    
    def semantic_description(self):
        return "Random condition node"
        

def random_bt(num_leaves:int,state:RandomState,seed:int=None,visualise:bool=False):
    if seed is not None:
        np.random.seed(seed)

    # Create random tree structure
    tree_graph = random_bt_structure(num_leaves)

    # Visualise the state graph
    if visualise:
        pos = graphviz_layout(tree_graph, prog="dot")
        nx.draw(tree_graph, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, font_color='black', arrows=True, pos=pos)
        plt.show()

    # Decide on input and output variables for each node
    node_inputs,node_outputs,node_actions = random_node_io(tree_graph, state)

    # Instantiate the tree
    tree = instantiate_tree(
        tree_graph=tree_graph,
        node_inputs=node_inputs,
        node_outputs=node_outputs,
        node_actions=node_actions,
        state=state)
    
    return tree
    

def random_bt_structure(num_leaves:int):
    G = nx.DiGraph()
    G.add_node("N0")


    num_children = {"N0":0}

    num_added_leaves = 1
    node_id = 1
    while num_added_leaves < num_leaves:
        if num_added_leaves == num_leaves - 1 and len(num_children.keys()) != 1:
            # Only need to add one more leaf, must be added to an internal node
            internal_nodes = [node for node in num_children.keys() if num_children[node] > 0]
            parent_node = np.random.choice(internal_nodes)
            G.add_node(f"N{node_id}")
            G.add_edge(parent_node, f"N{node_id}")
            num_children[parent_node] += 1
            num_children[f"N{node_id}"] = 0
            node_id += 1
        else:
            # Randomly select a node and add one or two children
            current_nodes = list(num_children.keys())
            parent_node = np.random.choice(current_nodes)

            if num_children[parent_node] == 0:
                # Is currently a leaf, so add two children
                G.add_node(f"N{node_id}")
                G.add_node(f"N{node_id+1}")
                G.add_edge(parent_node, f"N{node_id}")
                G.add_edge(parent_node, f"N{node_id+1}")
                num_children[parent_node] += 2
                num_children[f"N{node_id}"] = 0
                num_children[f"N{node_id+1}"] = 0
                node_id += 2
            else:
                # Is currently an internal node, so add one child
                G.add_node(f"N{node_id}")
                G.add_edge(parent_node, f"N{node_id}")
                num_children[parent_node] += 1
                num_children[f"N{node_id}"] = 0
                node_id += 1

        leaf_nodes = [node for node, children in num_children.items() if children == 0]
        num_added_leaves = len(leaf_nodes)

    return G

def random_node_io(tree_graph:nx.DiGraph, state:RandomState):
    node_inputs = {}
    node_outputs = {}
    node_actions = {}

    available_inputs = state.var_list
    available_outputs = state.internals
    available_actions = RandomAction.action_combos()

    for node in tree_graph.nodes:
        if tree_graph.out_degree(node) == 0:
            # Leaf node
            action = np.random.choice([True, False])
            if action:
                max_inputs = np.random.randint(0, len(available_inputs) + 1)
                node_inputs[node] = np.random.choice(available_inputs, size=max_inputs, replace=False).tolist()
                
                max_outputs = np.random.randint(1, len(available_outputs) + 1)
                node_outputs[node] = np.random.choice(available_outputs, size=max_outputs, replace=False).tolist()

                if node_inputs[node] == 0:
                    max_actions = 1
                else:
                    max_actions = np.random.randint(1, len(available_actions) + 1)
                node_actions[node] = np.random.choice(available_actions, size=max_actions, replace=False).tolist()

            else:
                max_inputs = np.random.randint(1, len(available_inputs) + 1)
                node_inputs[node] = np.random.choice(available_inputs, size=max_inputs, replace=False).tolist()

                node_outputs[node] = []
                node_actions[node] = []


    return node_inputs, node_outputs, node_actions

def instantiate_tree(tree_graph:nx.DiGraph, node_inputs:dict, node_outputs:dict, node_actions:dict, state:RandomState):
    node_seeds = {node: np.random.randint(0, 10000) for node in tree_graph.nodes}
    
    # Create BT nodes
    leaf_index = 0
    composite_index = 0
    nodes = {}
    for node in tree_graph.nodes:
        if tree_graph.out_degree(node) > 0:
            # Composite node
            node_class = np.random.choice([py_trees.composites.Selector, py_trees.composites.Sequence])
            node_bt = node_class(name=f"C{composite_index}",memory=False)
            composite_index += 1
        else:
            # Leaf node
            if node_actions[node] != []:
                # If there are actions, create a RandomActionNode
                node_bt = RandomActionNode(
                    inputs=node_inputs[node],
                    outputs=node_outputs[node],
                    actions=node_actions[node],
                    seed=node_seeds[node],
                    name=f"L{leaf_index}"
                )
            else:
                # If no actions, create a RandomConditionNode
                node_bt = RandomConditionNode(
                    inputs=node_inputs[node],
                    seed=node_seeds[node],
                    name=f"L{leaf_index}"
                )

            leaf_index += 1

        nodes[node] = node_bt

    # Connect nodes
    for parent, child in tree_graph.edges:
        nodes[parent].add_child(nodes[child])

    # Set the root node
    return py_trees.trees.BehaviourTree(root=nodes["N0"])

