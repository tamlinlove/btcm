import py_trees

from btcm.bt.nodes import ActionNode,ConditionNode
from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState
from btcm.examples.cognitive_sequence.cognitive_sequence import make_tree


def prompt_task_description():
    return '''
    The robot is tasked with running a cognitive exercise with a patient. The exercise consists of a serial recall game, where the robot displays a sequence of symbols and the user must accurately repeat the sequence back to the robot.
    The robot tracks several user factors, such as the user's frustration, engagement, task accuracy, reaction time, etc. in order to set the difficulty of the task, determine whether or not to repeat an exercise if the user has made a mistake, choose between social actions such as recapuring the attention of a distracted user or giving a hint, and deciding whether or not to end the entire exercise early.
    '''

def prompt_environment_description():
    state = CognitiveSequenceState()

    semantic_dict = state.semantic_dict()
    range_dict = state.get_range_dict()

    # Semantic description
    env_vars_list = [f"{var}:{semantic_dict[var]}" for var in semantic_dict]
    env_vars_text = ""
    for vartext in env_vars_list:
        env_vars_text += vartext + "\n"

    # Ranges
    env_range_list = [f"{var}:{range_dict[var].range_list()}" for var in range_dict]
    env_range_text = ""
    for vartext in env_range_list:
        env_range_text += vartext + "\n"

    return f'''
    The state consists of the following variables:

    {env_vars_text}

    These variables can take the following values

    {env_range_text}

    The following variables should never be included as reasons in any explanation: "CurrentSequence","UserSequence","AccuracySeed","ResponseTimeSeed"

    The variables in the state relate to each other in the following ways:

    UserConfusion is influenced by UserMemory and SequenceComplexity, such that UserConfusion is equal to 0.7 x UserMemory + 0.3 x a normalised SequenceComplexity
    UserEngagement is influenced by UserConfusion and UserAttention, such that UserEngagement is equal to 0.5 x (1-UserConfusion) + 0.5 x UserAttention
    BaseUserAccuracy is influenced by UserConfusion and SequenceComplexity, such that BaseUserAccuracy is equal to 0.2 x a normalised SequenceComplexity + 0.8 x (1-UserConfusion)
    UserNumErrors is influenced by AccuracySeed, SequenceLength and BaseUserAccuracy. First, an accuracy score is sampled from a normal distribution with mean BaseUserAccuracy and standard deviation 0.1, seeded with AccuracySeed. An accuracy score greater than 0.7 results in 0 errors. Otherwise, if it is greater than 0.4 it results in 1 error. Otherwise, if it is greater than 0.2 it results in 2 erros, and otherwise three errors. The number of errors cannot exceed the SequenceLength.
    BaseUserResponseTime is influenced by UserReactivity, UserConfusion, UserEngagement and SequenceLength. First, a time factor tf is calculated as 0.4 x UserReactivity + 0.2 x (1-UserConfusion) + 0.4 x UserEngagement. BaseUserResponseTime is then the SequenceLength x (1.6 - 1.2 x tf)
    ObservedUserResponseTime is influenced by BaseUserResponseTime and ResponseTimeSeed, such that ObservedUserResponseTime is sampled from a normal distribution with mean BaseUserResponseTime and standard deviation 1, seeded by ResponseTimeSeed
    UserFrustration is influenced by UserNumErrors and FeedbackGiven, such that if FeedbackGiven, then UserFrustration is updated to take the value (0.2 x UserNumErrors + 0.8) x UserFrustration + 0.05 x UserNumErrors. If FeedbackGiven is false, UserFrustration retains its original value.

    ResponseTimeSeed and AccuracySeed are continuously updated.

    All other variables stay static unless modified by the behaviour tree.
    '''

def prompt_bt_description():
    dummy_bt = make_tree()

    bt_node_text = ""
    for btnode in dummy_bt.root.iterate():
        if isinstance(btnode,ActionNode) or isinstance(btnode,ConditionNode):
            bt_node_text += f"Node name: {btnode.name}\n"
            bt_node_text += f"Node type: leaf node\n"
            bt_node_text += f"Node description: {btnode.detailed_semantic_description()}\n"
            bt_node_text += f"State variables read by node: {btnode.input_variables()}\n"
            bt_node_text += f"State variables written to by node: {btnode.output_variables()}\n"
            bt_node_text += f"Possible actions selected by node: {[action.name for action in btnode.action_space()]}\n"
            bt_node_text += "\n"
        else:
            if isinstance(btnode,py_trees.composites.Sequence):
                node_type = "Sequence"
            elif isinstance(btnode,py_trees.composites.Selector):
                node_type = "Fallback"

            bt_node_text += f"Node name: {btnode.name}\n"
            bt_node_text += f"Node type: {node_type}\n"
            bt_node_text += f"Node children: {[child.name for child in btnode.children]}\n"
            bt_node_text += "\n"

    return f'''
        The behaviour tree is composed of the following nodes:

        {bt_node_text}
    '''

def prompt_example_explanations():
    # TODO: Come up with examples that don't come from the same seeds as the experiment
    return f'''
    Example 1:

    User question: Why(decision_RepeatOrEnd=EndThisSequence,decision_RepeatOrEnd=RepeatThisSequence?,tick:5,time:101)
    Answer: [
    {{}}
    ]
    '''

def explainer_system_propmt(ep_mem:str):
    return f'''
        You are an explainable AI system designed to explain the behaviour of a robotic system controlled by a behaviour tree.
        You can explain the decisions taken by the robot, why particular behaviour tree nodes did or did not execute, the return statuses of behaviour tree nodes, and the values of variables representing factors in the environment state.
        In particular, your job is to compare two executions of the same robot in different contexts. Let's call these executions execution A and execution B.
        In execution B, something happened differently than what happened in execution A. The user will ask why the difference exists, referencing the specific difference that occurred.
        The user's query will take the following form:

        Why(OutcomeVar=P,OutcomeVar=Q,tick:i,time:j)

        You should interpret this query as the sentence "Why did variable OutcomeVar have the value of P at tick i, time j in execution B and not the value Q?"
        
        In order to provide counterfactual explanations in response to the user query, you have access to the following information:
        
        1. A textual description of the task
        2. A textual description of the environment state.
        3. A textual description of the behaviour tree, and how it interacts with the state.
        4. Episodic memory, in the form of a json file which describe the sequence of events in execution B.

        Below follows a textual description of the task:

        {prompt_task_description()}

        Below follows a textual description of the environment state:

        {prompt_environment_description()}

        Below follows a textual description of the behaviour tree, and how it interacts with the state:

        {prompt_bt_description()}

        Below follows the episodic memory describing the sequence of events that occurred in execution B, indexed by the tick and timestep of the behaviour tree and listing the value of state variables at each timestep as well as the last node executed, its decision and return status:

        {ep_mem}

        Given the above information, you must answer the user's query concisely and accurately, using only the information provided. 
        Your response must consist of a list of dictionary string swith the following fields: reason, intervention, counterfactual.
        Each of these three fields takes the following form: A string of the form "Var=X", where "Var" is the name of the relevant variable and "X" is the value of the variable

        The fields have the following meanings:
        - reason: "Var=X" implies that the fact that variable Var had value X in execution B resulted in the difference from execution A
        - intervention: "Var=Y" implies that changing the variable Var to have value Y instead of X would have resulted in the counterfactual outcome implied by the user's question
        - counterfactual: "OutcomeVar=Q" implies that the intervention in the "intervention" field has resulted in the variable OutcomeVar changing to Q from its real value of P, which satisfies the user's question

        Thus, your answer should look like this:

        [
        {{
        "reason":"Var1=X",
        "intervention":"Var1=Y",
        "counterfactual":"OutcomeVar=Q",
        }},
        {{
        "reason":"Var2=A",
        "intervention":"Var2=B",
        "counterfactual":"OutcomeVar=Q",
        }},
        ]

        You may include as many explanation dictionaries in the list as you need to completely explain the queried event, provided they are all correct and unique.

        Below are some examples of correctly formatted explanations.

        {prompt_example_explanations()}


    '''