import time
import py_trees

from btcm.examples.toy_examples import single_sequence
from btcm.cm.causalmodel import build_state_model
from btcm.bt.logger import Logger
from btcm.bt.btstate import BTStateManager

if __name__ == "__main__":
    '''
    Test State
    '''
    test_vals = {
        "VarA":0,
        "VarB":1,
        "VarC":1,
    }

    '''
    Tree
    '''
    board = single_sequence.setup_board(test_vals)
    tree = single_sequence.make_tree()

    '''
    Visitor
    '''
    logger = Logger(tree=tree,filename="log")
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
    
    '''
    Load BT
    '''
    manager = BTStateManager("log.json")

    '''
    # CM Test
    edges = [
        ("VarC","VarA")
    ]
    cm = build_state_model(state=board.state,edges=edges)
    cm.visualise()
    nm = cm.intervene(["VarC"],[0])
    nm.visualise()
    '''