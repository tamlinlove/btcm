import py_trees

from btcm.bt.btstate import BTStateManager
from btcm.cfx.explainer import Explainer

from btcm.examples.cognitive_sequence.dummy_env import DummyCognitiveSequenceEnvironment
from btcm.examples.cognitive_sequence.basic import SetSequenceParametersAction
from btcm.experiment import cognitive_sequence_experiment

if __name__ == "__main__":

    file = "cog_log_default.json"
    tick = 0
    time = "end" #97
    foils = [SetSequenceParametersAction("Medium","Simple"),SetSequenceParametersAction("Medium","Complex"),SetSequenceParametersAction("Long","Simple"),SetSequenceParametersAction("Long","Complex")]

    manager = BTStateManager(file,dummy_env=DummyCognitiveSequenceEnvironment(),directory=cognitive_sequence_experiment.LOG_DIRECTORY)
    manager.load_state(tick=tick,time="end")
    #manager.visualise_tree()
    #manager.visualise(show_values=True)
    #py_trees.display.render_dot_tree(manager.tree.root)


    explainer = Explainer(manager.model,node_names=manager.node_names)
    
    # Query set parameter decision
    node_id = manager.get_node_from_name("SetSequenceParameters","Decision")
    explainer.explain({node_id:foils},max_depth=1)