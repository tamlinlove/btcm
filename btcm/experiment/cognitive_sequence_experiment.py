from btcm.examples.cognitive_sequence import cognitive_sequence
from btcm.examples.cognitive_sequence.cognitive_sequence_environment import UserProfile
from btcm.bt.logger import Logger

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState

LOG_DIRECTORY = "logs/cognitive_sequence"

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
    logger = Logger(tree=tree,filename=f"{LOG_DIRECTORY}/{log_file}")
    tree.visitors.append(logger)    

    '''
    Run
    '''
    
    cognitive_sequence.run(tree=tree,board=board,display_tree=False)

'''
RUNNING EXPERIMENT FOR DIFFERENT USER PROFILES
'''
def run_default(filename:str="cog_log_default"):
    # Print
    print("==========================")
    print("Running default user profile experiment...")
    print("==========================")

    # Set up default state values and user profile
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

    # Run the experiment
    cognitive_sequence_run(
        initial_vals=initial_vals,
        user_profile=user_profile,
        log_file=filename,
    )

def run_perfect(filename:str="cog_log_default"):
    # Print
    print("==========================")
    print("Running perfect user profile experiment...")
    print("==========================")

    # Set up default state values and user profile
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

    # Tweak to match a perfect user
    user_profile.memory = 1
    user_profile.reactivity = 1
    user_profile.attention = 1

    # Run the experiment
    cognitive_sequence_run(
        initial_vals=initial_vals,
        user_profile=user_profile,
        log_file=filename,
    )

def run_worst(filename:str="cog_log_default"):
    # Print
    print("==========================")
    print("Running worst user profile experiment...")
    print("==========================")

    # Set up default state values and user profile
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

    # Tweak to match a very bad user
    user_profile.memory = 0
    user_profile.reactivity = 0
    user_profile.attention = 0

    # Run the experiment
    cognitive_sequence_run(
        initial_vals=initial_vals,
        user_profile=user_profile,
        log_file=filename,
    )

def run_no_attention(filename:str="cog_log_default"):
    # Print
    print("==========================")
    print("Running no_attention user profile experiment...")
    print("==========================")

    # Set up default state values and user profile
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

    # Tweak to match a user with no attention span
    user_profile.attention = 0

    # Run the experiment
    cognitive_sequence_run(
        initial_vals=initial_vals,
        user_profile=user_profile,
        log_file=filename,
    )

def run_no_reactivity(filename:str="cog_log_default"):
    # Print
    print("==========================")
    print("Running no_reactivity user profile experiment...")
    print("==========================")

    # Set up default state values and user profile
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

    # Tweak to match a user with no reactivity
    user_profile.reactivity = 0

    # Run the experiment
    cognitive_sequence_run(
        initial_vals=initial_vals,
        user_profile=user_profile,
        log_file=filename,
    )