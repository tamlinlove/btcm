import py_trees

from btcm.examples.toy_examples import case_study

from btcm.bt.logger import Logger
from btcm.bt.btstate import BTStateManager
from btcm.cfx.explainer import Explainer
from btcm.cfx.query_manager import QueryManager

LOG_DIR = "logs/case_study"

if __name__ == "__main__":
    # Run
    vals = {
        "X_a":False,
        "X_b":True,
        "X_c":True,
        "X_d":False,
    }

    board = case_study.setup_board(vals=vals)
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

    #manager.visualise_tree()
    #manager.visualise(show_values=True)

    explainer = Explainer(manager.model,node_names=manager.node_names)
    query_manager = QueryManager(explainer,manager,visualise=False,visualise_only_valid=False)

    # Query parameters
    '''
    # Case Study Return
    nodename = "L0"
    nodetype = "Return"
    tick = 0
    time = 1
    foils = [py_trees.common.Status.SUCCESS]
    '''

    nodename = "CaseStudyFallback"
    nodetype = "Return"
    tick = 0
    time = 4
    foils = [py_trees.common.Status.SUCCESS]

    query = query_manager.make_query(nodename,nodetype,tick=tick,time=time,foils=foils,action_foil_all_but_null=False)

    explanations = explainer.explain(query,max_depth=2,visualise=False,visualise_only_valid=False)
    print(f"{len(explanations)} explanations found")
    for exp in explanations:
        print(f"-----{exp.text(names=manager.pretty_node_names())}")