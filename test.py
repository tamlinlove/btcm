import time
import py_trees

from btcm.examples.toy_examples import single_sequence

if __name__ == "__main__":
    '''
    Test State
    '''
    test_vals = {
        "VarA":1,
        "VarB":1,
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