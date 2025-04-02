import time
import py_trees

from btcm.examples.cognitive_sequence import cognitive_sequence
from btcm.cm.causalmodel import build_state_model
from btcm.bt.logger import Logger

if __name__ == "__main__":
    '''
    Initial Game State
    '''
    test_vals = {
        "EndGame":False,
        "NumSequences":0,
        "SequenceSet":False,
    }

    '''
    Tree
    '''
    board = cognitive_sequence.setup_board(test_vals)
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
            tree.tick()
            time.sleep(0.5)
            finished = tree.root.status != py_trees.common.Status.RUNNING
    except KeyboardInterrupt:
        print("KILL")
        pass