import py_trees
import time
import networkx as nx

from btcm.examples.random.random_state import RandomState
from btcm.examples.random.random_bt import random_bt

def random_domain(
        num_vars:int,
        connectivity:float,
        num_leaves:int,
        top_ratio:float=0.5,
        internal_ratio:float=0.25,
        seed:int=None,
        display:bool=False,
):
    board = setup_board(
        num_vars=num_vars,
        connectivity=connectivity,
        top_ratio=top_ratio,
        internal_ratio=internal_ratio,
        seed=seed,
        display=display
    )

    tree = make_tree(
        num_leaves=num_leaves,
        state=board.state,
        seed=seed,
        visualise=display
    )

    return board, tree

def setup_board(num_vars:int,connectivity:float,top_ratio:float,internal_ratio:float,seed:int=None,display=True):
    board = py_trees.blackboard.Client(name="Board")
    board.register_key("state", access=py_trees.common.Access.WRITE)
    board.register_key("display", access=py_trees.common.Access.WRITE)

    # State
    state = RandomState(
        num_vars=num_vars,
        connectivity=connectivity,
        top_ratio=top_ratio,
        internal_ratio=internal_ratio,
        seed=seed,
        visualise=False
    )
    board.state = state

    # Other experiment parameters
    board.display = display

    return board

def make_tree(num_leaves:int,state:RandomState,seed:int=None, visualise:bool=False):
    return random_bt(num_leaves=num_leaves, state=state, seed=seed, visualise=visualise)

def reconstruct_random_tree(filename:str,directory:str="logs/random/",data:dict=None):
    '''
    Recreate a random tree from a file.
    '''
    # Parse filename
    flist = filename.split("_")
    run_name = flist[1]
    seed = int(flist[3])
    num_vars = int(flist[5])
    cm_connectivity = float(flist[7])
    num_leaves = int(flist[9].split(".")[0])

    # Reconstruct the tree
    state = RandomState(
        num_vars=num_vars,
        connectivity=cm_connectivity,
        top_ratio=0.5,
        internal_ratio=0.25,
        seed=seed,
        visualise=False
    )
    tree = random_bt(num_leaves=num_leaves, state=state, seed=seed, visualise=False)

    # Read in ids from data
    node_ids = {}
    if data is not None:
        # NOTE: Assumes all nodes in the tree have a unique name
        for id in data["tree"]:
            node_ids[data["tree"][id]["name"]] = id

    # Reconstruct the tree graph
    graph = nx.DiGraph()
    behaviours = {} # Maps node name to behaviour object
    behaviours_to_nodes = {} # Maps behaviour object to node name

    def add_nodes_and_edges(node):
        if data is None:
            node_id = node.name
        else:
            node_id = node_ids[node.name]

        graph.add_node(node_id)
        behaviours[node_id] = node
        behaviours_to_nodes[node] = node_id
        for child in node.children:
            if data is None:
                child_id = child.name
            else:
                child_id = node_ids[child.name]

            graph.add_edge(node_id, child_id)
            add_nodes_and_edges(child)

    add_nodes_and_edges(tree.root)

    return graph, tree, behaviours, behaviours_to_nodes

    
def make_state(filename,directory:str="logs/random/"):
    # Parse filename
    flist = filename.split("_")
    run_name = flist[1]
    seed = int(flist[3])
    num_vars = int(flist[5])
    cm_connectivity = float(flist[7])
    num_leaves = int(flist[9].split(".")[0])

    state = RandomState(
        num_vars=num_vars,
        connectivity=cm_connectivity,
        top_ratio=0.5,
        internal_ratio=0.25,
        seed=seed,
        visualise=False
    )

    return state

def state_class():
    return RandomState

'''
RUN TREE
'''
def run(tree:py_trees.trees.BehaviourTree,display_tree:bool=False):
    tree.setup()
    try:
        # Tick the tree
        tree.tick()
        # Sleep for a bit to simulate time passing
        time.sleep(0.1)
        # Optional, print the tree structure
        if display_tree:
            print(py_trees.display.unicode_tree(tree.root, show_status=True))
    except KeyboardInterrupt:
        print("KILL")
        pass