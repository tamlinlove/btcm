import argparse

from btcm.bt.btstate import BTStateManager
from btcm.cfx.explainer import Explainer

from btcm.examples.cognitive_sequence.dummy_env import DummyCognitiveSequenceEnvironment
from btcm.examples.cognitive_sequence.basic import SetSequenceParametersAction
from btcm.experiment import cognitive_sequence_experiment

if __name__ == "__main__":
    '''
    Parse Arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profile', type=str, required=True)
    parser.add_argument('-f', '--filename', type=str)
    parser.add_argument('--visualise',  action='store_true')
    args = parser.parse_args()

    '''
    Validation and Defaults
    '''
    # Profile
    profile_name = args.profile.lower()
    if profile_name not in cognitive_sequence_experiment.profile_experiments:
        raise ValueError(f"Profile {args.profile} is not valid")
    
    # Filename
    filename = args.filename
    if args.filename is None:
        filename = f"cog_log_{profile_name}"
    
    '''
    Load file and BT
    '''

    file = f"{filename}.json"
    tick = 0
    time = 4 #"end" #97
    foils = None

    print("Reconstructing behaviour tree from logs...")
    manager = BTStateManager(file,dummy_env=DummyCognitiveSequenceEnvironment(),directory=cognitive_sequence_experiment.LOG_DIRECTORY)

    print("Loading state at specified time...")
    manager.load_state(tick=tick,time=time)
    if args.visualise:
        print("Displaying visualisations")
        manager.visualise_tree()
        manager.visualise(show_values=True)
        #py_trees.display.render_dot_tree(manager.tree.root)


    print("Loading explainer...")
    explainer = Explainer(manager.model,node_names=manager.node_names)
    
    # Query set parameter decision
    print("Generating explanations...")
    node_id = manager.get_node_from_name("SetSequenceParameters","Decision")
    explainer.explain({node_id:foils},max_depth=1)