import py_trees
import networkx as nx

from typing import Dict

from btcm.bt.nodes import Leaf,ActionNode,ConditionNode

class TreeNode:
    def __init__(self,name:str,category:str):
        self.name = name
        self.category = category
        self.status = py_trees.common.Status.INVALID

    def to_dict(self) -> dict:
        return {
            "name":self.name,
            "category":self.category,
            "status":str(self.status),
        }


class Logger(py_trees.visitors.VisitorBase):
    def __init__(self, full:bool = False, tree: py_trees.trees.BehaviourTree = None) -> None:
        super().__init__(full)

        self.tick = 0 # The current tick iteration
        self.time = 0 # The current timestep which increments after each leaf execution

        self.root = None # The root of the tree, for visualisation
        self.tree = tree # Points to the tree itself

        # Create dict of tree nodes and types
        self.make_tree(tree)

    '''
    TREE STATE FUNCTIONS
    '''
    def make_tree(self,tree:py_trees.trees.BehaviourTree):
        self.nodes: Dict[str,TreeNode] = {}
        self.graph = nx.DiGraph()
        self.ranges = {}
        self.var_funcs = {}

        self.add_to_tree(tree.root)

    def add_to_tree(self,btnode:py_trees.behaviour.Behaviour):
        # Get node category
        if isinstance(btnode,ActionNode):
            category = "Action"
        elif isinstance(btnode,ConditionNode):
            category = "Condition"
        elif isinstance(btnode,py_trees.composites.Sequence):
            category = "Sequence"
        else:
            raise TypeError(f"Unsuported behaviour of type {type(btnode)}")

        # Add node to structure
        self.nodes[btnode.id] = TreeNode(
            name=btnode.name,
            category=category
        )

        # Add node to graph
        self.graph.add_node(btnode.id)

        # Recursively add children
        for child in btnode.children:
            self.add_to_tree(child)
            # Add child edge to structure
            self.graph.add_edge(btnode.id,child.id)

    '''
    VISITOR FUNCTIONS
    '''

    def initialise(self) -> None:
        self.visited = {}
        self.root = None

    def run(self, behaviour: py_trees.behaviour.Behaviour):
        # Runs as each behaviour is ticked
        self.root = behaviour

        # Update stored behaviours
        self.nodes[behaviour.id].status = behaviour.status


        # Old Log
        '''
        if isinstance(behaviour,Leaf):
            print(f"T{self.tick}:t{self.time} - {behaviour.name}")
            self.log()
            self.time += 1
            self.reconstruct_tree_state()
        '''

        # Log
        if self.nodes[behaviour.id].category in ["Action","Condition"]:
            # Leaf node, log
            self.log()
            self.time += 1

    def log(self):
        # TODO: This should save the state to a file or something
        log_dict = {
            "tick":self.tick,
            "time":self.time,
            "nodes":{}
        }
        for node in self.nodes:
            log_dict["nodes"][str(node)] = self.nodes[node].to_dict()

        # TODO: Add state to log
        # TODO: Save log to file
        print(log_dict)

    def reconstruct_tree_state(self):
        # Given the known states of all terminated nodes, reconstruct the full state of the tree
        self.print_behaviour_status(self.tree.root)

    def print_behaviour_status(self,behaviour: py_trees.behaviour.Behaviour):
        print(behaviour.name,behaviour.status.value)
        for child in behaviour.children:
            self.print_behaviour_status(child)

    def finalise(self) -> None:
        # Runs after each tick of the tree
        self.tick += 1