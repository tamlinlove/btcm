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

    '''
    ALTERNATE CONSTRUCTOR
    '''
    @staticmethod
    def default_user():
        default_state = CognitiveSequenceState.default_values()
        return UserProfile(
            speed=default_state["UserSpeed"],
            accuracy=default_state["UserAccuracy"],
            attention=default_state["UserAttention"],
            frustration=default_state["UserFrustration"],
            confusion=default_state["UserConfusion"]
        )

    '''
    TYPING
    '''

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
        # TODO: FOR FASTER DEBUGGING OVERRIDING MAX_TIMEOUT, REMOVE LATER
        max_timeout = 4

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
    def robot_speak(self, text:str):
        # Simulate the robot speaking
        print(f"ROBOT SAYS: {text}")

    def user_speak(self, text:str):
        # Simulate the user speaking
        print(f"USER SAYS: {text}")

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

        return max(substring_score, pairwise_score)
    
    def get_hint(self):
        # Compare the true sequence and the user's sequence
        true_sequence = self.sequence
        user_sequence = self.user_sequence

        # Check if the user has responded at all
        if user_sequence is None:
            return "Don't forget to repeat the sequence back to me!"

        # Check for length mismatch
        if len(user_sequence) < len(true_sequence):
            return f"Your response was too short, it should be {len(true_sequence)} characters long."
        elif len(user_sequence) > len(true_sequence):
            return f"Your response was too long, it should be {len(true_sequence)} characters long."

        # Check for mistakes in the sequence
        beginning_threshold = int(len(true_sequence) * 0.3)  # First few characters
        end_threshold = int(len(true_sequence) * 0.7)  # Last few characters

        for i, (true_char, user_char) in enumerate(zip(true_sequence, user_sequence)):
            if true_char != user_char:
                if i < beginning_threshold:
                    return "You made a mistake at the beginning."
                elif i >= end_threshold:
                    return "You started well, but there was a mistake at the end."
                else:
                    return f"You made a mistake around the middle, near position {i + 1}."

        # If no specific hint can be generated
        return "Listen carefully to the sequence again. You can do it!"

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
    
    def provide_sequence(self,state:CognitiveSequenceState):
        if not state.vals["SequenceSet"]:
            # Sequence not set!
            return False
        # Provide the sequence to the user
        if state.vals["NumRepetitions"] == 0:
            # First time for this unique sequence
            if state.vals["NumSequences"] > 1:
                # Second, third, etc. unique sequence
                self.robot_speak(f"Here is the new sequence. Listen carefully. {self.sequence}")
            else:
                # First time for this unique sequence
                self.robot_speak(f"Here is the sequence. Listen carefully. {self.sequence}")
        else:
            # Sequence has been repeated
            self.robot_speak(f"Here is the sequence again. Listen carefully. {self.sequence}")

        return True
    
    def reset_timer(self):
        # Ask the user to respond
        self.robot_speak("Ok, now it's your turn. Please repeat the sequence.")

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

        return True
    
    def check_timer(self,state:CognitiveSequenceState):
        # Get time
        curr_time = time.time()
        elapsed_time = min(int(curr_time - self.user_response_timer),CognitiveSequenceState.MAX_TIMEOUT)

        # Set elapsed time in state
        state.vals["UserResponseTime"] = elapsed_time

        # Check if the user has responded
        if elapsed_time > self.user_response_time:
            # User has responded
            state.vals["UserResponded"] = True
            self.user_speak(self.user_sequence)
        else:
            # User has not responded yet
            state.vals["UserResponded"] = False

    def assess_user_sequence(self,state:CognitiveSequenceState):
        # If no response, set accuracy to "CompletelyWrong" and speed to "Slower"
        if not state.vals["UserResponded"]:
            state.vals["LatestUserAccuracy"] = "CompletelyWrong"
            state.vals["LatestUserSpeed"] = "Slower"
            return

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

    '''
    SOCIAL ACTIONS
    '''
    def give_hint(self,state:CognitiveSequenceState):
        # Sentence before hint
        if state.vals["LatestUserAccuracy"] in ["CompletelyWrong", "Poor"]:
            self.robot_speak("Hmmm...that's not quite right. Let me give you a hint.")
        elif state.vals["LatestUserAccuracy"] == "Medium":
            self.robot_speak("You're getting there! Here's a little hint to help you out.")
        elif state.vals["LatestUserAccuracy"] == "Good":
            self.robot_speak("You're doing well! Here's a hint to guide you.")
        else:
            # Shouldn't give a hint here!
            return False
        
        # Provide hint
        self.robot_speak(self.get_hint())
        return True
    
    def repeat_sequence_social_action(self,state:CognitiveSequenceState):
        if state.vals["LatestUserAccuracy"] == "Perfect":
            # Can't repeat a perfect sequence!
            return False

        # The sequence will be repeated, provide encouragement based on user's latest accuracy and their confusion level
        # Check if the user responded
        if not state.vals["UserResponded"]:
            if self.user_profile.confusion == "High":
                self.robot_speak("It seems like you missed that. Don't worry, let's try again together!")
            else:
                self.robot_speak("No response? That's okay, let's give it another shot!")
        else:
            # Provide encouragement based on accuracy and confusion
            if state.vals["LatestUserAccuracy"] in ["CompletelyWrong", "Poor"]:
                if self.user_profile.confusion == "High":
                    self.robot_speak("That was a bit tricky, wasn't it? Let's go through it again.")
                else:
                    self.robot_speak("Not quite right... Let's try again.")
            elif state.vals["LatestUserAccuracy"] == "Medium":
                if self.user_profile.confusion == "High":
                    self.robot_speak("You're getting there! Let's repeat it carefully.")
                else:
                    self.robot_speak("That was close! Let's go over it again to perfect it.")
            elif state.vals["LatestUserAccuracy"] == "Good":
                if self.user_profile.confusion == "High":
                    self.robot_speak("Great effort! Let's repeat it once more to make sure.")
                else:
                    self.robot_speak("You're doing really well! Let's go over it again to get it 100 percent right.")
        return True
    
    def end_sequence_social_action(self,state:CognitiveSequenceState):
        # Ending the sequence, provide some congratulations or consolation
        if state.vals["LatestUserAccuracy"] == "Perfect":
            self.robot_speak("Fantastic job! You nailed it!")
        elif state.vals["LatestUserAccuracy"] in ["Good", "Medium"]:
            self.robot_speak("Great effort! You're really getting the hang of this.")
        elif state.vals["LatestUserAccuracy"] == "Poor":
            self.robot_speak("Don't worry, we all have off days.")
        else:
            self.robot_speak("That's okay, we'll get it next time!")
        return True
    
    def recapture_attention(self,state:CognitiveSequenceState):
        # Check if the user responded or not, and try to recapture their attention accordingly
        if state.vals["UserResponded"]:
            self.robot_speak("You seem distracted. Let's focus on the task at hand.")
        else:
            self.robot_speak("Hey there! I need your attention!")
        return True
        

