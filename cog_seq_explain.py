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
    #explainer.explain({"return_8c27a2b2-c0f8-482b-a340-196102ad26c6":[py_trees.common.Status.SUCCESS]},max_depth=None)
    explainer.explain({"decision_50ec0b0e-21d5-4886-9187-b5c6813ac75a":None},max_depth=1)