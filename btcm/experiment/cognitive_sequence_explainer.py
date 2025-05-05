import py_trees

from btcm.bt.btstate import BTStateManager
from btcm.cfx.explainer import Explainer
from btcm.cfx.query_manager import QueryManager
from btcm.examples.cognitive_sequence.dummy_env import DummyCognitiveSequenceEnvironment
from btcm.experiment import cognitive_sequence_experiment

def explain_single(
        profile_name: str,
        file: str,
        nodename: str,
        nodetype: str,
        tick: int,
        time: int,
        max_depth: int = 1,
        visualise: bool = False,
):
    # Reconstruct BT
    manager = BTStateManager(file,dummy_env=DummyCognitiveSequenceEnvironment(),directory=cognitive_sequence_experiment.LOG_DIRECTORY)

    # Load State
    manager.load_state(tick=tick,time=time)

    if visualise:
        manager.visualise_tree()
        manager.visualise(show_values=True)
        #py_trees.display.render_dot_tree(manager.tree.root)

    # Load explainer
    explainer = Explainer(manager.model,node_names=manager.node_names)

    # Set up the query and foils
    query_manager = QueryManager(explainer,manager,visualise=visualise)
    foils = None # TODO: add arguments that can be passed to the query manager to make interesting foils
    query = query_manager.make_query(nodename,nodetype,foils=foils)

    # Explain
    explainer.explain(query,max_depth=max_depth,visualise=visualise)