import time
import py_trees

from btcm.bt.btstate import BTStateManager
from btcm.cfx.explainer import Explainer

if __name__ == "__main__":
    manager = BTStateManager("cog_log.json")
    manager.load_state(tick=0,time="end")
    manager.visualise(show_values=True)

    explainer = Explainer(manager.model)
    #explainer.explain({"return_8c27a2b2-c0f8-482b-a340-196102ad26c6":[py_trees.common.Status.SUCCESS]},max_depth=None)
    explainer.explain({"executed_049c355a-dfea-4304-949f-74818f411759":[True]},max_depth=1)