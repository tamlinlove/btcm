import py_trees
import time

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState
from btcm.examples.cognitive_sequence.cognitive_sequence_environment import CognitiveSequenceEnvironment,UserProfile
from btcm.examples.cognitive_sequence.initial_checks import initial_checks_subtree

'''
BLACKBOARD
'''
def setup_board(vals:dict=None,user_profile:UserProfile=None,skip=False):
    board = py_trees.blackboard.Client(name="Board")
    board.register_key("state", access=py_trees.common.Access.WRITE)
    board.register_key("environment", access=py_trees.common.Access.WRITE)

    # State
    if vals is None:
        vals = CognitiveSequenceState.default_values()
    state = CognitiveSequenceState(vals)
    board.state = state

    # Environment
    if user_profile is None:
        user_profile = UserProfile.default_user()
    env = CognitiveSequenceEnvironment(user_profile=user_profile,skip=skip)
    board.environment = env

    # User Profile
    user_profile.update_state(board.state)

    return board

'''
BT ROOT
'''
def make_tree():
    return py_trees.trees.BehaviourTree(root=initial_checks_subtree())

'''
RUN TREE
'''
def run(tree:py_trees.trees.BehaviourTree, board:py_trees.blackboard.Client,display_tree:bool=False):
    tree.setup()
    try:
        finished = False
        while not finished:
            # Tick the tree
            tree.tick()
            # Sleep for a bit to simulate time passing
            time.sleep(0.5)
            # Check if the game is over
            finished = board.environment.game_over
            # Optional, print the tree structure
            if display_tree:
                print(py_trees.display.unicode_tree(tree.root, show_status=True))
    except KeyboardInterrupt:
        print("KILL")
        pass