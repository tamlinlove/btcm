import time
import py_trees

from btcm.bt.btstate import BTStateManager
from btcm.cfx.explainer import Explainer

if __name__ == "__main__":
    manager = BTStateManager("log.json")
    manager.load_state(tick=0,time="end")
    manager.visualise(show_values=True)

    explainer = Explainer(manager.model)
    #explainer.explain({"decision_f81601d8-199f-426b-8657-fe7c3bae808b":None})
    # NB: this is hardcoded for now, so if you re-generate the log.json you will have to manually change the variable you are querying below
    explainer.explain({"return_064e92cc-eff3-4a38-bff8-59f5b9ae4df3":[py_trees.common.Status.SUCCESS]},max_depth=2)
