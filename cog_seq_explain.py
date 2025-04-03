import time
import py_trees

from btcm.bt.btstate import BTStateManager
from btcm.cfx.explainer import Explainer

if __name__ == "__main__":
    manager = BTStateManager("cog_log.json")
    manager.load_state(tick=0,time="end")
    manager.visualise_tree()
    manager.visualise(show_values=True)

    explainer = Explainer(manager.model)
    
    # Query set parameter decision
    node_id = manager.get_node_from_name("SetSequenceParameters","Decision")
    explainer.explain({node_id:None},max_depth=1)