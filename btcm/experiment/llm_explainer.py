import json

from btcm.bt.btstate import BTStateManager
from btcm.cfx.comparer import Comparer
from btcm.examples.cognitive_sequence.dummy_env import DummyCognitiveSequenceEnvironment
from btcm.experiment import cognitive_sequence_experiment
from btcm.experiment.llm_utils import explainer_system_propmt


def llm_explain():
    '''
    LLM generates an explanation using the following information

    * the episodic memory, passed using files
    * description of BT structure and functions
    * description of State model and functions
    * The difference to be explained
    '''

def llm_compare(
        file1: str,
        file2: str,
        target_profile: str,
        log_dir1:str=cognitive_sequence_experiment.LOG_DIRECTORY,
        log_dir2:str=cognitive_sequence_experiment.LOG_DIRECTORY,
        hide_display: bool = False,
):
    # Reconstruct BT
    manager1 = BTStateManager(file1,dummy_env=DummyCognitiveSequenceEnvironment(),directory=log_dir1)
    manager2 = BTStateManager(file2,dummy_env=DummyCognitiveSequenceEnvironment(),directory=log_dir2)

    # Compare
    comparer = Comparer(manager1,manager2)

    target_var = cognitive_sequence_experiment.profile_targets[target_profile]

    # First, check if there is a difference in executions
    same,difference,u1,u2 = comparer.find_first_difference()

    if same:
        # TODO: what do we return?
        return
    
    # There is a difference, pass to LLM
    
    # Read episodic memory from file
    with open(f"{log_dir2}/{file2}") as epmem_json:
        data = json.load(epmem_json)
        data.pop("tree",None)
        data.pop("state",None)
        data.pop("environment",None)

    llm_system_prompt = explainer_system_propmt(str(data))
    print(llm_system_prompt)