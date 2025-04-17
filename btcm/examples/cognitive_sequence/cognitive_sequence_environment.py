import time
import numpy as np

from btcm.dm.environment import Environment
from btcm.dm.action import NullAction

from btcm.examples.cognitive_sequence.basic import SetSequenceParametersAction,CognitiveSequenceState

'''
SIMULATED USER
'''
class UserProfile():
    def __init__(self, memory:float=0, attention:float=0, reactivity:float=0, initial_frustration:float=0.2):
        # Profile characteristics
        self.memory = memory # The capacity for the user to remember
        self.attention = attention # The attention span of the user
        self.reactivity = reactivity # The ability for the user to react quickly
        self.initial_frustration = initial_frustration


    '''
    ALTERNATE CONSTRUCTOR
    '''
    @staticmethod
    def default_user():
        default_state = CognitiveSequenceState.default_values()
        return UserProfile(
            memory = default_state["UserMemory"],
            attention = default_state["UserAttention"],
            reactivity = default_state["UserReactivity"],
            initial_frustration = default_state["UserFrustration"]
        )

    '''
    UTILITY
    '''
    def update_state(self,state:CognitiveSequenceState):
        state.set_value("UserMemory", self.memory)
        state.set_value("UserAttention", self.attention)
        state.set_value("UserReactivity", self.reactivity)
        state.set_value("UserFrustration", self.initial_frustration)

    '''
    USER SIMULATION
    '''
    @staticmethod
    def generate_sequence(state:CognitiveSequenceState):
        # Start with the true sequence
        user_sequence = state.get_value("CurrentSequence")

        if state.get_value("UserNumErrors") == 0:
            return user_sequence

        random_indices = np.random.choice(len(user_sequence), state.get_value("UserNumErrors"), replace=False)

        sequence_list = list(user_sequence)

        for index in random_indices:
            errors = ["drop","replace"]
            error_type = np.random.choice(errors)

            if error_type == "drop":
                # Randomly drop a character
                sequence_list[index] = None # Will drop later
            else:
                # Randomly replace a character with another symbol
                character_set = ["A","B","C","D"]
                allowed_characters = character_set[0:state.get_value("SequenceComplexity")]
                allowed_characters.remove(sequence_list[index]) # Not the same symbol

                sequence_list[index] = np.random.choice(allowed_characters)

        modified_list = [symbol for symbol in sequence_list if symbol is not None]
        return ''.join(modified_list)
    
    def update_frustration(self,state:CognitiveSequenceState):
        state.set_value("UserFrustration",CognitiveSequenceState.get_frustration(state))

'''
ENVIRONMENT
'''
class CognitiveSequenceEnvironment(Environment):
    def __init__(self,user_profile:UserProfile,skip:bool=False,display:bool=True):
        super().__init__()
        self.user_profile = user_profile
        self.skip = skip
        self.display = display

        # Internal State
        self.game_over = False
        
        # User
        self.user_responding = False
        self.user_response_timer = None
        self.user_sequence = None

        # Skip
        self.first_check = False


    '''
    ENVIRONMENT FUNCTIONS
    '''
    def robot_speak(self, text:str):
        # Simulate the robot speaking
        if self.display:
            print(f"ROBOT SAYS: {text}")

    def user_speak(self, text:str):
        # Simulate the user speaking
        if self.display:
            print(f"USER SAYS: {text}")

    def env_speak(self, text:str):
        # Asides from the environments
        if self.display:
            print(f"[{text}]")
    
    '''
    ROBOT ACTIONS
    '''
    def end_game(self):
        self.game_over = True
        return True
    
    def provide_sequence(self,state:CognitiveSequenceState):
        # Provide the sequence to the user
        if state.get_value("NumRepetitions") == 0:
            # First time for this unique sequence
            if state.get_value("NumSequences") > 1:
                # Second, third, etc. unique sequence
                self.robot_speak(f"Here is the new sequence. Listen carefully. {state.get_value("CurrentSequence")}")
            else:
                # First time for this unique sequence
                self.robot_speak(f"Here is the sequence. Listen carefully. {state.get_value("CurrentSequence")}")
        else:
            # Sequence has been repeated
            self.robot_speak(f"Here is the sequence again. Listen carefully. {state.get_value("CurrentSequence")}")

        # Update user response now that new sequence is here
        state.set_value("UserResponded",False)

        # Update user variables based on the new sequence
        state.set_value("UserConfusion",CognitiveSequenceState.get_confusion(state))
        state.set_value("UserEngagement",CognitiveSequenceState.get_engagement(state))
        state.set_value("BaseUserAccuracy",CognitiveSequenceState.get_accuracy(state))
        state.set_value("UserNumErrors",CognitiveSequenceState.get_num_errors(state))
        state.set_value("BaseUserResponseTime",CognitiveSequenceState.get_time(state))
        state.set_value("ObservedUserResponseTime",CognitiveSequenceState.get_observed_time(state))
        state.set_value("UserSequence",UserProfile.generate_sequence(state))

        # Update seeds
        state.set_value("AccuracySeed",np.random.randint(0,1000000000))
        state.set_value("ResponseTimeSeed",np.random.randint(0,1000000000))

        return True
    
    def reset_timer(self,state:CognitiveSequenceState):
        # Ask the user to respond
        self.robot_speak("Ok, now it's your turn. Please repeat the sequence.")

        # Update variables
        self.user_responding = True
        self.user_response_timer = time.time()
        self.first_check = False

        state.set_value("UserResponded",False)
        state.set_value("UserTimeout",False)

        return True
    
    def check_timer(self,state:CognitiveSequenceState):
        # Get time
        if self.skip and self.first_check:
            curr_time = time.time() + CognitiveSequenceState.MAX_TIMEOUT + 1
        else:
            curr_time = time.time()
        elapsed_time = curr_time - self.user_response_timer

        # Check if the user has responded
        if elapsed_time > state.get_value("ObservedUserResponseTime"):
            if elapsed_time >= CognitiveSequenceState.MAX_TIMEOUT and state.get_value("ObservedUserResponseTime")>=CognitiveSequenceState.MAX_TIMEOUT:
                # Timeout
                state.set_value("UserResponded",False)
                state.set_value("UserTimeout",True)
            else:
                # User has responded
                state.set_value("UserResponded",True)
                self.user_speak(state.get_value("UserSequence"))
                self.env_speak(f"User responded in {state.get_value("ObservedUserResponseTime")} seconds")
        else:
            # User has not responded yet
            state.set_value("UserResponded",False)

        self.first_check = True

    '''
    SOCIAL ACTIONS
    '''
    def give_hint(self,state:CognitiveSequenceState):
        if state.get_value("UserNumErrors") == 0:
            self.robot_speak("You don't need any help, you're doing great!")
        elif state.get_value("UserNumErrors") == 1:
            self.robot_speak("Almost right, you made only one mistake.")
        else:
            self.robot_speak(f"Hmmm...that's not quite right. Here's a hint: you made {str(state.get_value("UserNumErrors"))} mistakes.")

        # Update frustration
        self.user_profile.update_frustration(state)

        return True
    
    def repeat_sequence_social_action(self,state:CognitiveSequenceState):
        if not state.get_value("UserResponded"):
            # No response
            self.robot_speak("No response? That's okay, let's give it another shot!")
        else:
            sentences = [
                "ERROR: Can't repeat a perfect sequence",
                "Nice, that was very close. Let's try again and get it perfect!",
                "Not quite right... Let's try again.",
                "Hmmm... no, that's not it. Let's try again."
            ]

            self.robot_speak(sentences[state.get_value("UserNumErrors")])

        # Update frustration
        self.user_profile.update_frustration(state)
    
    def end_sequence_social_action(self,state:CognitiveSequenceState):
        if not state.get_value("UserResponded"):
            # No response
            self.robot_speak("No response? That's a pity...")
        else:
            sentences = [
                "Fantastic job! You nailed it!",
                "Great effort, that was really close to the right answer!",
                "Not quite right... we all make mistakes.",
                "Don't worry, we all have off days."
            ]

            self.robot_speak(sentences[state.get_value("UserNumErrors")])

        # Update frustration
        self.user_profile.update_frustration(state)
    
    def recapture_attention(self,state:CognitiveSequenceState):
        # Check if the user responded or not, and try to recapture their attention accordingly
        if state.get_value("UserResponded"):
            self.robot_speak("You seem distracted. Let's focus on the task at hand.")
        else:
            self.robot_speak("Hey there! I need your attention!")

        # Update frustration
        self.user_profile.update_frustration(state)

        return True
        

