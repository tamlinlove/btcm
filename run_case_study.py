from btcm.examples.toy_examples import case_study

from btcm.bt.logger import Logger
from btcm.bt.btstate import BTStateManager

LOG_DIR = "logs/case_study"

if __name__ == "__main__":
    # Run
    board = case_study.setup_board()
    tree = case_study.make_tree()

    log_file = "case_study"
    logger = Logger(tree=tree,filename=f"{LOG_DIR}/{log_file}",log_env=False)
    tree.visitors.append(logger)  

    case_study.run(tree=tree, display_tree=False)

    # Explain
    manager = BTStateManager(
        f"{log_file}.json",
        directory=LOG_DIR,
        no_env=True
        )
    
    manager.load_state(tick=0,time="end")

    manager.visualise_tree()
    manager.visualise(show_values=True)

    for edge in manager.model.graph.edges:
        print(manager.node_names[edge[0]],"-",manager.node_names[edge[1]])