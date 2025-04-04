import random
import time

from btcm.dm.environment import Environment
from btcm.dm.action import NullAction

from btcm.examples.cognitive_sequence.basic import SetSequenceParametersAction,CognitiveSequenceState

'''
SIMULATED USER
'''
class UserProfile():
    def __init__(self, speed:str, accuracy:str, attention:str, frustration:str, confusion:str):
        self.speed = speed
        self.accuracy = accuracy
        self.attention = attention
        self.frustration = frustration
        self.confusion = confusion

    def __str__(self):
        return f"UserProfile(speed={self.speed}, accuracy={self.accuracy}, attention={self.attention}, frustration={self.frustration}, confusion={self.confusion})"

    '''
    USER SIMULATION
    '''
    def calculate_response_time(self,sequence_length:str,sequence_complexity:str,max_timeout:int = 10):
        # Define base response times for different sequence lengths and complexities
        base_times = {
            "Short": {"Simple": 0.2*max_timeout, "Complex": 0.3*max_timeout},
            "Medium": {"Simple": 0.4*max_timeout, "Complex": 0.6*max_timeout},
            "Long": {"Simple": 0.6*max_timeout, "Complex": 0.9*max_timeout}
        }

        # Get the base response time based on sequence length and complexity
        base_time = base_times[sequence_length][sequence_complexity]

        # Adjust the base time based on user speed
        if self.speed == "Fast":
            base_time *= 0.8
        elif self.speed == "Slow":
            base_time *= 1.2

        # Adjust the base time based on user attention
        if self.attention == "High":
            base_time *= 0.9
        elif self.attention == "Low":
            base_time *= 1.1

        # Add some randomness to simulate variability in response times
        if self.attention == "High":
            response_time = int(base_time + random.uniform(-1, 1))
        elif self.attention == "Medium":
            response_time = int(base_time + random.uniform(-1, 1.2))
        elif self.attention == "Low":
            response_time = int(base_time + random.uniform(-1, 2))

        # Ensure the response time is within a reasonable range
        response_time = max(1, min(response_time, max_timeout))

        return response_time

'''
ENVIRONMENT
'''
class CognitiveSequenceEnvironment(Environment):
    def __init__(self,user_profile:UserProfile):
        super().__init__()
        self.user_profile = user_profile

        # Internal State
        self.game_over = False
        self.number_of_sequences = 0
        self.sequence_length = None
        self.sequence_complexity = None
        self.sequence = ""
        
        # User
        self.user_responding = False
        self.user_response_timer = None
        self.user_response_time = None


    '''
    ENVIRONMENT FUNCTIONS
    '''
    def generate_sequence(self):
        if self.sequence_length is None or self.sequence_complexity is None:
            raise ValueError("Sequence length and complexity must be set before generating a sequence.")
        
        # Generate a sequence based on the parameters
        if self.sequence_complexity == "Simple":
            characters = ["A", "B"]
        elif self.sequence_complexity == "Complex":
            characters = ["A", "B", "C", "D"]
        else:
            raise ValueError("Invalid complexity level. Choose 'Simple' or 'Complex'.")

        if self.sequence_length == "Short":
            seq_length = 3
        elif self.sequence_length == "Medium":
            seq_length = 6
        elif self.sequence_length == "Long":
            seq_length = 9
        else:
            raise ValueError("Invalid length. Choose 'Short', 'Medium', or 'Long'.")

        sequence = [random.choice(characters) for _ in range(seq_length)]
        return ''.join(sequence)

    '''
    ROBOT ACTIONS
    '''
    def end_game(self):
        self.game_over = True
        return True
    
    def set_sequence(self,set_params_action:SetSequenceParametersAction):
        if set_params_action == NullAction():
            return False

        # Set the parameters in the state
        self.sequence_length = set_params_action.sequence_length
        self.sequence_complexity = set_params_action.sequence_complexity
        self.sequence = self.generate_sequence()

        return True
    
    def reset_timer(self):
        # Update variables
        self.user_responding = True
        self.user_response_timer = time.time()
        # Determine the time the user will take based on their profile
        self.user_response_time = self.user_profile.calculate_response_time(
            self.sequence_length,
            self.sequence_complexity,
            max_timeout=CognitiveSequenceState.MAX_TIMEOUT
        ) 

        print("Setting user response time to: ", self.user_response_time)

        return True
    
    def check_timer(self,state:CognitiveSequenceState):
        # Get time
        curr_time = time.time()
        elapsed_time = min(int(curr_time - self.user_response_timer),state.MAX_TIMEOUT)

        # Set elapsed time in state
        state.vals["UserResponseTime"] = elapsed_time

        # Check if the user has responded
        if elapsed_time > self.user_response_time:
            # User has responded
            state.vals["UserResponded"] = True
        else:
            # User has not responded yet
            state.vals["UserResponded"] = False

