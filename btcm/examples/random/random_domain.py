import py_trees
import time

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