import argparse

from btcm.bt.btstate import BTStateManager
from btcm.cfx.explainer import Explainer
from btcm.cfx.query_manager import QueryManager

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
    parser.add_argument('-v', '--vis_option', type=str, default="no")
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

    nodename = "SequenceLength_1"
    nodetype = "State"
    tick = 0
    time = 4
    foils = None #[6]

    '''
    nodename = "SetSequenceParameters"
    nodetype = "Decision"
    tick = 0
    time = 4
    foils = None
    '''

    '''
    nodename = "DecideSocialAction"
    nodetype = "Decision"
    tick = 1
    time = 27
    foils = None
    '''

    print("Reconstructing behaviour tree from logs...")
    manager = BTStateManager(file,dummy_env=DummyCognitiveSequenceEnvironment(),directory=cognitive_sequence_experiment.LOG_DIRECTORY)

    print("Loading state at specified time...")
    manager.load_state(tick=tick,time=time)
    if args.visualise:
        print("Displaying visualisations")
        #manager.visualise_tree()
        #manager.visualise(show_values=True)
        #py_trees.display.render_dot_tree(manager.tree.root)


    print("Loading explainer...")
    explainer = Explainer(manager.model,node_names=manager.node_names)

    # Set up the query
    query_manager = QueryManager(explainer,manager,visualise=args.visualise)
    query = query_manager.make_query(nodename,nodetype,foils=foils)
    
    # Query set parameter decision
    print("Generating explanations...")
    explainer.explain(query,max_depth=1,visualise=args.visualise)