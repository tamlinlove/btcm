import time
import py_trees

from btcm.examples.cognitive_sequence import cognitive_sequence
from btcm.cm.causalmodel import build_state_model
from btcm.bt.logger import Logger

from btcm.examples.cognitive_sequence.cognitive_sequence_environment import UserProfile

if __name__ == "__main__":

    '''
    User Profile
    '''
    user_profile = UserProfile(
        speed="Fast",
        accuracy="High",
        attention="High",
        frustration="Low",
        confusion="Low"
    )

    '''
    Initial Game State
    '''
    test_vals = {
        # Game state variables
        "EndGame":False,
        "NumRepetitions":0,
        "SequenceSet":False,
        "ResponseTimerActive":False,
        "UserResponded": False,
        "UserResponseTime": 0,
        "LatestUserAccuracy":"Good",
        "LatestUserSpeed":"Faster",
        "AttemptedReengageUser":False,
        "RepeatSequence":False,
        "NumSequences":0,

        # User progress variables
        "UserAccuracy":"High",
        "UserSpeed":"Fast",

        # User state variables
        "UserAttention":"Low",
        "UserFrustration":"Low",
        "UserConfusion":"Low",
    }

    '''
    Tree
    '''
    board = cognitive_sequence.setup_board(test_vals,user_profile=user_profile)
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