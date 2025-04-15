import time
import numpy as np

from btcm.dm.environment import Environment
from btcm.dm.action import NullAction

from btcm.examples.cognitive_sequence.basic import SetSequenceParametersAction,CognitiveSequenceState

'''
SIMULATED USER
'''
class UserProfile():
    def __init__(self, memory:float=0, attention:float=0, reactivity:int=0):
        # Profile characteristics
        self.memory = memory # The capacity for the user to remember
        self.attention = attention # The attention span of the user
        self.reactivity = reactivity # The ability for the user to react quickly


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
        )

    '''
    USER SIMULATION
    '''
    def generate_sequence(self,state:CognitiveSequenceState):
        # Start with the true sequence
        user_sequence = state.vals["CurrentSequence"]

        if state.vals["UserNumErrors"] == 0:
            return user_sequence

        random_indices = np.random.choice(len(user_sequence), state.vals["UserNumErrors"], replace=False)

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
                allowed_characters = character_set[0:state.vals["SequenceComplexity"]]
                allowed_characters.remove(sequence_list[index]) # Not the same symbol

                sequence_list[index] = np.random.choice(allowed_characters)

        modified_list = [symbol for symbol in sequence_list if symbol is not None]
        return ''.join(modified_list)

'''
ENVIRONMENT
'''
class CognitiveSequenceEnvironment(Environment):
    def __init__(self,user_profile:UserProfile):
        super().__init__()
        self.user_profile = user_profile

        # Internal State
        self.game_over = False
        
        # User
        self.user_responding = False
        self.user_response_timer = None
        self.user_sequence = None

        self.user_accuracy = None
        self.user_base_response_time = None
        self.user_observed_response_time = None


    '''
    ENVIRONMENT FUNCTIONS
    '''
    def robot_speak(self, text:str):
        # Simulate the robot speaking
        print(f"ROBOT SAYS: {text}")

    def user_speak(self, text:str):
        # Simulate the user speaking
        print(f"USER SAYS: {text}")
    
    '''
    ROBOT ACTIONS
    '''
    def end_game(self):
        self.game_over = True
        return True
    
    def provide_sequence(self,state:CognitiveSequenceState):
        # Provide the sequence to the user
        if state.vals["NumRepetitions"] == 0:
            # First time for this unique sequence
            if state.vals["NumSequences"] > 1:
                # Second, third, etc. unique sequence
                self.robot_speak(f"Here is the new sequence. Listen carefully. {state.vals["CurrentSequence"]}")
            else:
                # First time for this unique sequence
                self.robot_speak(f"Here is the sequence. Listen carefully. {state.vals["CurrentSequence"]}")
        else:
            # Sequence has been repeated
            self.robot_speak(f"Here is the sequence again. Listen carefully. {state.vals["CurrentSequence"]}")

        # Update user response now that new sequence is here
        state.vals["UserResponded"] = False

        # Update user variables based on the new sequence
        state.vals["UserConfusion"] = CognitiveSequenceState.get_confusion(state)
        state.vals["UserEngagement"] = CognitiveSequenceState.get_engagement(state)
        state.vals["BaseUserAccuracy"] = CognitiveSequenceState.get_accuracy(state)
        state.vals["UserNumErrors"] = CognitiveSequenceState.get_num_errors(state)
        state.vals["BaseUserResponseTime"] = CognitiveSequenceState.get_time(state)
        state.vals["ObservedUserResponseTime"] = CognitiveSequenceState.get_observed_time(state)

        return True
    
    def reset_timer(self,state:CognitiveSequenceState):
        # Ask the user to respond
        self.robot_speak("Ok, now it's your turn. Please repeat the sequence.")

        # Update variables
        self.user_responding = True
        self.user_response_timer = time.time()

        return True
    
    def check_timer(self,state:CognitiveSequenceState):
        # Get time
        curr_time = time.time()
        elapsed_time = min(int(curr_time - self.user_response_timer),CognitiveSequenceState.MAX_TIMEOUT)

        # Check if the user has responded
        if elapsed_time > self.user_response_time:
            # User has responded
            state.vals["UserResponded"] = True
            self.user_speak(self.user_sequence)
        else:
            # User has not responded yet
            state.vals["UserResponded"] = False

    def reset_sequence_state(self,state:CognitiveSequenceState):
        # End the current sequence, reset for new sequence
        state.vals["NumRepetitions"] = 0
        state.vals["SequenceSet"] = False
        state.vals["ResponseTimerActive"] = False
        state.vals["UserResponded"] = False
        state.vals["UserResponseTime"] = 0
        state.vals["AttemptedReengageUser"] = False
        state.vals["RepeatSequence"] = False

        # Check if we have reached the maximum number of sequences
        if state.vals["NumSequences"] >= state.MAX_NUM_SEQUENCES:
            state.vals["EndGame"] = True

        # To help with reading terminal output
        print("---------------")

        return True

    '''
    SOCIAL ACTIONS
    '''
    def give_hint(self,state:CognitiveSequenceState):
        if state.vals["UserNumErrors"] == 0:
            self.robot_speak("You don't need any help, you're doing great!")
        elif state.vals["UserNumErrors"] == 1:
            self.robot_speak("Almost right, you made only one mistake.")
        else:
            self.robot_speak(f"Hmmm...that's not quite right. Here's a hint: you made {str(state.vals["UserNumErrors"])} mistakes.")

        return True
    
    def repeat_sequence_social_action(self,state:CognitiveSequenceState):
        if not state.vals["UserResponded"]:
            # No response
            self.robot_speak("No response? That's okay, let's give it another shot!")
        else:
            sentences = [
                "ERROR: Can't repeat a perfect sequence",
                "Nice, that was very close. Let's try again and get it perfect!",
                "Not quite right... Let's try again.",
                "Hmmm... no, that's not it. Let's try again."
            ]

            self.robot_speak(sentences[state.vals["UserNumErrors"]])
    
    def end_sequence_social_action(self,state:CognitiveSequenceState):
        if not state.vals["UserResponded"]:
            # No response
            self.robot_speak("No response? That's a pity...")
        else:
            sentences = [
                "Fantastic job! You nailed it!",
                "Great effort, that was really close to the right answer!",
                "Not quite right... we all make mistakes.",
                "Don't worry, we all have off days."
            ]

            self.robot_speak(sentences[state.vals["UserNumErrors"]])
    
    def recapture_attention(self,state:CognitiveSequenceState):
        # Check if the user responded or not, and try to recapture their attention accordingly
        if state.vals["UserResponded"]:
            self.robot_speak("You seem distracted. Let's focus on the task at hand.")
        else:
            self.robot_speak("Hey there! I need your attention!")

        return True
        

