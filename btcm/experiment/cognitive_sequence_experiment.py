from btcm.examples.cognitive_sequence import cognitive_sequence
from btcm.examples.cognitive_sequence.cognitive_sequence_environment import UserProfile
from btcm.bt.logger import Logger

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState

'''
BASIC RUN EXPERIMENT
'''

def cognitive_sequence_run(initial_vals:dict,user_profile:UserProfile,log_file:str="cog_log"):
    '''
    Tree
    '''
    board = cognitive_sequence.setup_board(vals=initial_vals,user_profile=user_profile)
    tree = cognitive_sequence.make_tree()

    '''
    Visitor
    '''
    logger = Logger(tree=tree,filename=log_file)
    tree.visitors.append(logger)    

    '''
    Run
    '''
    
    cognitive_sequence.run(tree=tree,board=board,display_tree=False)

'''
RUNNING EXPERIMENT FOR DIFFERENT USER PROFILES
'''
def run_default():
    # Print
    print("==========================")
    print("Running default user profile experiment...")
    print("==========================")

    # Set up default state values and user profile
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

     # Tweak the user profile to be more average
    user_profile.accuracy = "Medium"
    user_profile.speed = "Medium"

    # Run the experiment
    cognitive_sequence_run(
        initial_vals=initial_vals,
        user_profile=user_profile,
        log_file="cog_log_default"
    )
    

def run_distracted():
    # Print
    print("==========================")
    print("Running distracted user profile experiment...")
    print("==========================")

    # Set up default state values and user profile
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

    # Tweak the user profile to be distracted
    initial_vals["UserAttention"] = "Low"
    user_profile.attention = "Low"

    # Run the experiment
    cognitive_sequence_run(
        initial_vals=initial_vals,
        user_profile=user_profile,
        log_file="cog_log_distracted"
    )

def run_slow():
    # Print
    print("==========================")
    print("Running slow user profile experiment...")
    print("==========================")

    # Set up default state values and user profile
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

    # Tweak the user profile to be slow
    user_profile.speed = "Slow"

    # Run the experiment
    cognitive_sequence_run(
        initial_vals=initial_vals,
        user_profile=user_profile,
        log_file="cog_log_slow"
    )