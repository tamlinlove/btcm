import time
import py_trees

from btcm.examples.toy_examples import single_sequence
from btcm.cm.statemodel import StateModel

def varAfunc(VarC=None):
    return VarC

def varBfunc(VarC=None):
    return VarC

if __name__ == "__main__":
    '''
    Test State
    '''
    test_vals = {
        "VarA":1,
        "VarB":0,
        "VarC":1,
    }

    '''
    Tree
    '''
    board = single_sequence.setup_board(test_vals)
    tree = single_sequence.make_tree()

    '''
    Run
    '''
    print(f"State: {board.state}")
    try:
        finished = False
        while not finished:
            tree.tick()
            time.sleep(0.5)
            finished = tree.root.status != py_trees.common.Status.RUNNING
    except KeyboardInterrupt:
        print("KILL")
        pass

    # CM Test
    vfs = {
        "VarA":varAfunc,
        "VarB":varBfunc,
        "VarC":None,
    }
    cm = StateModel(board.state,var_funcs=vfs)
    cm.add_edge(["VarC","VarA"])
    #cm.add_edge(["VarC","VarB"])
    cm.nodes["VarA"].run("VarC")
    cm.visualise()
    nm = cm.intervene(["VarA"],[0])
    nm.visualise()