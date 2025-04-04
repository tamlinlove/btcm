import py_trees

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState
from btcm.examples.cognitive_sequence.cognitive_sequence_environment import CognitiveSequenceEnvironment,UserProfile
from btcm.examples.cognitive_sequence.initial_checks import initial_checks_subtree

'''
BLACKBOARD
'''
def setup_board(vals:dict,user_profile:UserProfile):
    board = py_trees.blackboard.Client(name="Board")
    board.register_key("state", access=py_trees.common.Access.WRITE)
    board.register_key("environment", access=py_trees.common.Access.WRITE)

    # State
    state = CognitiveSequenceState(vals)
    board.state = state

    # Environment
    env = CognitiveSequenceEnvironment(user_profile=user_profile)
    board.environment = env

    return board

'''
BT ROOT
'''
def make_tree():
    return py_trees.trees.BehaviourTree(root=initial_checks_subtree())