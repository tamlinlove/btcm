import py_trees

from btcm.bt.btstate import BTStateManager
from btcm.cfx.explainer import Explainer
from btcm.cfx.query_manager import QueryManager
from btcm.cfx.comparer import Comparer
from btcm.examples.cognitive_sequence.dummy_env import DummyCognitiveSequenceEnvironment
from btcm.experiment import cognitive_sequence_experiment

def display(text,hide_display:bool=False):
    if not hide_display:
        print(text)
    else:
        pass

def explain_single(
        file: str,
        nodename: str,
        nodetype: str,
        tick: int,
        time: int,
        foils: list = None,
        max_depth: int = 1,
        visualise: bool = False,
        visualise_only_valid: bool = False,
        hide_display: bool = False,
):
    # Reconstruct BT
    manager = BTStateManager(file,dummy_env=DummyCognitiveSequenceEnvironment(),directory=cognitive_sequence_experiment.LOG_DIRECTORY)

    # Load State
    manager.load_state(tick=tick,time=time)

    manager.save_graph_to_file("bt_graph.txt")
    if visualise:
        manager.visualise_tree()
        manager.visualise(show_values=True)
        #py_trees.display.render_dot_tree(manager.tree.root)

    # Load explainer
    explainer = Explainer(manager.model,node_names=manager.node_names)

    # Set up the query and foils

    query_manager = QueryManager(explainer,manager,visualise=visualise,visualise_only_valid=visualise_only_valid)
    query = query_manager.make_query(nodename,nodetype,foils=foils)
    display(f"\n=====QUERY=====\n{query_manager.query_text(query)}",hide_display=hide_display)

    # Explain
    display("\n=====EXPLANATION=====",hide_display=hide_display)
    explainer.explain(query,max_depth=max_depth,visualise=visualise,visualise_only_valid=visualise_only_valid)

def compare_runs(
        file1: str,
        file2: str,
        target_profile: str,
        max_follow_ups: int = 2,
        max_depth: int = 1,
        visualise: bool = False,
        visualise_only_valid: bool = False,
        hide_display: bool = False,
):
    # Reconstruct BT
    manager1 = BTStateManager(file1,dummy_env=DummyCognitiveSequenceEnvironment(),directory=cognitive_sequence_experiment.LOG_DIRECTORY)
    manager2 = BTStateManager(file2,dummy_env=DummyCognitiveSequenceEnvironment(),directory=cognitive_sequence_experiment.LOG_DIRECTORY)

    # Compare
    comparer = Comparer(manager1,manager2)

    target_var = cognitive_sequence_experiment.profile_targets[target_profile]
    comparer.explain_follow_ups(target_var=target_var,max_follow_ups=max_follow_ups,max_depth=max_depth,visualise=visualise,visualise_only_valid=visualise_only_valid,hide_display=hide_display)