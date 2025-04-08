import time
import py_trees

from btcm.examples.cognitive_sequence import cognitive_sequence
from btcm.cm.causalmodel import build_state_model
from btcm.bt.logger import Logger

from btcm.examples.cognitive_sequence.cognitive_sequence_environment import UserProfile
from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState

if __name__ == "__main__":

    '''
    Tweak Default State and User
    '''
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

    '''
    Tree
    '''
    board = cognitive_sequence.setup_board(vals=initial_vals,user_profile=user_profile)
    tree = cognitive_sequence.make_tree()

    '''
    Visitor
    '''
    logger = Logger(tree=tree,filename="cog_log")
    tree.visitors.append(logger)    

    '''
    Run
    '''
    
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
            #print(py_trees.display.unicode_tree(tree.root, show_status=True))
    except KeyboardInterrupt:
        print("KILL")
        pass