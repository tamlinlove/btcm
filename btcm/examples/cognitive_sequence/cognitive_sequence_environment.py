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
    def generate_sequence(self,true_sequence,sequence_length:str,sequence_complexity:str):
        # Start with the true sequence
        user_sequence = list(true_sequence)

        # Error rate based on complexity and accuracy
        error_rate_dict = {
            "Simple": {
                "High": 0.01,
                "Medium": 0.1,
                "Low": 0.2
            },
            "Complex": {
                "High": 0.1,
                "Medium": 0.2,
                "Low": 0.35
            }
        }

        error_rate = error_rate_dict[sequence_complexity][self.accuracy]

        # Introduce errors based on accuracy
        for i in range(len(user_sequence)):
            if random.random() < error_rate:
                # Replace with a random character from the allowed set
                if sequence_complexity == "Simple":
                    allowed_characters = ["A", "B"]
                elif sequence_complexity == "Complex":
                    allowed_characters = ["A", "B", "C", "D"]
                else:
                    raise ValueError("Invalid complexity level. Choose 'Simple' or 'Complex'.")
                
                user_sequence[i] = random.choice(allowed_characters)

        # Shuffle rate based on confusion and length
        shuffle_rate_dict = {
            "Short": {
                "High": 0.15,
                "Medium": 0.1,
                "Low": 0.01
            },
            "Medium": {
                "High": 0.25,
                "Medium": 0.18,
                "Low": 0.03
            },
            "Long": {
                "High": 0.3,
                "Medium": 0.25,
                "Low": 0.05
            }
        }

        shuffle_rate = shuffle_rate_dict[sequence_length][self.confusion]

        if random.random() < shuffle_rate:
            random.shuffle(user_sequence)

        # Drop rate based on attention and length
        drop_rate_dict = {
            "Short": {
                "High": 0.01,
                "Medium": 0.02,
                "Low": 0.08
            },
            "Medium": {
                "High": 0.03,
                "Medium": 0.06,
                "Low": 0.12
            },
            "Long": {
                "High": 0.05,
                "Medium": 0.1,
                "Low": 0.2
            }
        }

        drop_rate = drop_rate_dict[sequence_length][self.attention]

        user_sequence = [
            char for char in user_sequence if random.random() > drop_rate
        ]

        # Ensure the sequence is not empty
        if not user_sequence:
            user_sequence = [random.choice(true_sequence)]

        return ''.join(user_sequence)
    
    def get_base_response_times(self,max_timeout:int = 10):
        # Define base response times for different sequence lengths and complexities
        base_times = {
            "Short": {"Simple": 0.2*max_timeout, "Complex": 0.3*max_timeout},
            "Medium": {"Simple": 0.4*max_timeout, "Complex": 0.6*max_timeout},
            "Long": {"Simple": 0.6*max_timeout, "Complex": 0.9*max_timeout}
        }
        return base_times

    def calculate_response_time(self,sequence_length:str,sequence_complexity:str,max_timeout:int = 10):
        base_times = self.get_base_response_times(max_timeout)

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
        self.user_sequence = None


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
    
    def calculate_substring_score(self, string_a: str, string_b: str) -> float:
        if not string_a or not string_b:
            return 0.0

        # Find the longest common substring using dynamic programming
        len_a, len_b = len(string_a), len(string_b)
        dp = [[0] * (len_b + 1) for _ in range(len_a + 1)]
        max_length = 0

        for i in range(1, len_a + 1):
            for j in range(1, len_b + 1):
                if string_a[i - 1] == string_b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    max_length = max(max_length, dp[i][j])

        # Calculate similarity score based on the longest common substring
        total_length = len_a + len_b
        similarity_score = (2 * max_length) / total_length

        return similarity_score
    
    def calculate_pairwise_score(self, string_a: str, string_b: str) -> float:
        if not string_a or not string_b:
            return 0.0

        # Calculate the pairwise score based on the number of matching characters
        matches = sum(1 for a, b in zip(string_a, string_b) if a == b)
        total_length = max(len(string_a), len(string_b))
        similarity_score = matches / total_length

        return similarity_score
    
    def calculate_similarity_score(self, string_a: str, string_b: str) -> float:
        # Calculate the substring score and pairwise score
        substring_score = self.calculate_substring_score(string_a, string_b)
        pairwise_score = self.calculate_pairwise_score(string_a, string_b)

        print(f"Score: {substring_score}, {pairwise_score}: {max(substring_score, pairwise_score)}")

        return max(substring_score, pairwise_score)

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

        self.user_sequence = self.user_profile.generate_sequence(
            self.sequence,
            self.sequence_length,
            self.sequence_complexity
        )

        print("Setting user response time to: ", self.user_response_time)
        print("True sequence: ", self.sequence)
        print("User sequence: ", self.user_sequence)

        return True
    
    def check_timer(self,state:CognitiveSequenceState):
        # Get time
        curr_time = time.time()
        elapsed_time = min(int(curr_time - self.user_response_timer),CognitiveSequenceState.MAX_TIMEOUT)

        print("Elapsed time: ", elapsed_time)

        # Set elapsed time in state
        state.vals["UserResponseTime"] = elapsed_time

        # Check if the user has responded
        if elapsed_time > self.user_response_time:
            # User has responded
            state.vals["UserResponded"] = True
        else:
            # User has not responded yet
            state.vals["UserResponded"] = False

    def assess_user_sequence(self,state:CognitiveSequenceState):
        # Assess Speed
        base_times = self.user_profile.get_base_response_times(max_timeout=CognitiveSequenceState.MAX_TIMEOUT)
        if self.user_response_time < 0.9*base_times[self.sequence_length][self.sequence_complexity]:
            # User is faster than expected
            comparative_speed = "Faster"
        elif self.user_response_time > 1.1*base_times[self.sequence_length][self.sequence_complexity]:
            # User is slower than expected
            comparative_speed = "Slower"
        else:
            # User is within expected range
            comparative_speed = "Normal"
        state.vals["LatestUserSpeed"] = comparative_speed

        # Assess Accuracy
        score = self.calculate_similarity_score(self.sequence, self.user_sequence)

        # Update latest accuracy
        if score == 1.0:
            state.vals["LatestUserAccuracy"] = "Perfect"
        elif score >= 0.8:
            state.vals["LatestUserAccuracy"] = "Good"
        elif score >= 0.5:
            state.vals["LatestUserAccuracy"] = "Medium"
        elif score >= 0.1:
            state.vals["LatestUserAccuracy"] = "Poor"
        else:
            state.vals["LatestUserAccuracy"] = "CompletelyWrong"

