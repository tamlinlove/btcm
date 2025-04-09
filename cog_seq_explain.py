from btcm.bt.btstate import BTStateManager
from btcm.cfx.explainer import Explainer

from btcm.examples.cognitive_sequence.cognitive_sequence_environment import UserProfile
from btcm.examples.cognitive_sequence.dummy_env import DummyCognitiveSequenceEnvironment

from btcm.examples.cognitive_sequence.basic import SetSequenceParametersAction

if __name__ == "__main__":

    file = "cog_log_slow.json"
    tick = 17
    foils = [SetSequenceParametersAction("Medium","Simple"),SetSequenceParametersAction("Medium","Complex"),SetSequenceParametersAction("Long","Simple"),SetSequenceParametersAction("Long","Complex")]

    manager = BTStateManager(file,dummy_env=DummyCognitiveSequenceEnvironment())
    manager.load_state(tick=tick,time="end")
    #manager.visualise_tree()
    #manager.visualise(show_values=True)

    explainer = Explainer(manager.model,node_names=manager.node_names)
    
    # Query set parameter decision
    node_id = manager.get_node_from_name("SetSequenceParameters","Decision")
    explainer.explain({node_id:foils},max_depth=2)