from btcm.examples.cognitive_sequence import cognitive_sequence
from btcm.examples.cognitive_sequence.cognitive_sequence_environment import UserProfile
from btcm.bt.logger import Logger

from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState

LOG_DIRECTORY = "logs/cognitive_sequence"

'''
BASIC RUN EXPERIMENT
'''

def cognitive_sequence_run(
        initial_vals:dict,
        user_profile:UserProfile,
        log_file:str="cog_log",
        skip:bool=False,
        display:bool=True,
        log_dir:str=LOG_DIRECTORY,
        seed_override:tuple[int,int]=None,
    ):
    '''
    Tree
    '''
    board = cognitive_sequence.setup_board(
        vals=initial_vals,
        user_profile=user_profile,
        skip=skip,
        display=display,
        seed_override=seed_override
    )
    tree = cognitive_sequence.make_tree()

    '''
    Visitor
    '''
    logger = Logger(tree=tree,filename=f"{log_dir}/{log_file}")
    tree.visitors.append(logger)    

    '''
    Run
    '''
    
    cognitive_sequence.run(tree=tree,board=board,display_tree=False)

'''
RUNNING EXPERIMENT FOR DIFFERENT USER PROFILES
'''
def run_default(filename:str="cog_log_default",display=True,**kwargs):
    # Print
    if display:
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
        display=display,
        **kwargs,
    )

def run_perfect(filename:str="cog_log_perfect",display=True,**kwargs):
    # Print
    if display:
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
        display=display,
        **kwargs,
    )

def run_worst(filename:str="cog_log_worst",display=True,**kwargs):
    # Print
    if display:
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
        display=display,
        **kwargs
    )

def run_no_attention(filename:str="cog_log_no_attention",display=True,**kwargs):
    # Print
    if display:
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
        display=display,
        **kwargs
    )

def run_no_memory(filename:str="cog_log_no_memory",display=True,**kwargs):
    # Print
    if display:
        print("==========================")
        print("Running no_memory user profile experiment...")
        print("==========================")

    # Set up default state values and user profile
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

    # Tweak to match a user with no attention span
    user_profile.memory = 0

    # Run the experiment
    cognitive_sequence_run(
        initial_vals=initial_vals,
        user_profile=user_profile,
        log_file=filename,
        display=display,
        **kwargs
    )

def run_no_reactivity(filename:str="cog_log_no_reactivity",display=True,**kwargs):
    # Print
    if display:
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
        display=display,
        **kwargs
    )

def run_frustrated(filename:str="cog_log_frustrated",display=True,**kwargs):
    # Print
    if display:
        print("==========================")
        print("Running frustrated user profile experiment...")
        print("==========================")

    # Set up default state values and user profile
    initial_vals = CognitiveSequenceState.default_values()
    user_profile = UserProfile.default_user()

    # Tweak to match a user with very high frustration
    user_profile.initial_frustration = 0.8

    # Run the experiment
    cognitive_sequence_run(
        initial_vals=initial_vals,
        user_profile=user_profile,
        log_file=filename,
        display=display,
        **kwargs
    )


'''
PROFILES
'''
profile_experiments = {
    "default":run_default,
    "perfect":run_perfect,
    "worst":run_worst,
    "no_attention":run_no_attention,
    "no_reactivity":run_no_reactivity,
    "no_memory":run_no_memory,
    "frustrated":run_frustrated,
}

profile_targets = {
    "default":None,
    "perfect":None,
    "worst":None,
    "no_attention":"UserAttention",
    "no_reactivity":"UserReactivity",
    "no_memory":"UserMemory",
    "frustrated":"UserFrustration",
}