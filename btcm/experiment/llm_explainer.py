import json
import py_trees
import ollama
import timeit

from btcm.bt.btstate import BTStateManager
from btcm.cfx.comparer import Comparer
from btcm.examples.cognitive_sequence.dummy_env import DummyCognitiveSequenceEnvironment
from btcm.experiment import cognitive_sequence_experiment
from btcm.cfx.query_manager import QueryManager
from btcm.cfx.explainer import Explainer,AggregatedCounterfactualExplanation
from btcm.experiment.llm_utils import explainer_system_propmt,prompt_example_explanations
from btcm.examples.cognitive_sequence.basic import CognitiveSequenceState


def llm_explain():
    '''
    LLM generates an explanation using the following information

    * the episodic memory, passed using files
    * description of BT structure and functions
    * description of State model and functions
    * The difference to be explained
    '''

def llm_compare(
        file1: str,
        file2: str,
        target_profile: str,
        log_dir1:str=cognitive_sequence_experiment.LOG_DIRECTORY,
        log_dir2:str=cognitive_sequence_experiment.LOG_DIRECTORY,
        model_name:str="phi4",
        hide_display: bool = False,
):
    # Reconstruct BT
    manager1 = BTStateManager(file1,dummy_env=DummyCognitiveSequenceEnvironment(),directory=log_dir1)
    manager2 = BTStateManager(file2,dummy_env=DummyCognitiveSequenceEnvironment(),directory=log_dir2)

    # Compare
    comparer = Comparer(manager1,manager2)

    target_var = cognitive_sequence_experiment.profile_targets[target_profile]

    # First, check if there is a difference in executions
    same,difference,u1,u2 = comparer.find_first_difference()

    if same:
        return False, None
    
    # There is a difference, pass to LLM
    
    # Read episodic memory from file
    with open(f"{log_dir2}/{file2}") as epmem_json:
        data = json.load(epmem_json)
        data.pop("tree",None)
        data.pop("state",None)
        data.pop("environment",None)

    llm_system_prompt = explainer_system_propmt(str(data))
    #llm_system_prompt = explainer_system_propmt("")
    
    # Extract query
    manager2.load_state(tick=u2.tick, time=u2.time)
    node_names = manager2.pretty_node_names()

    explainer = Explainer(manager2.model, node_names=node_names, history=manager2.value_history)
    query_manager = QueryManager(explainer, manager2, visualise=False, visualise_only_valid=False)

    # Get the query for the first difference
    if difference == "name":
        # TODO: Can query why the node didn't execute????
        raise NotImplementedError("Name comparison not implemented")
    elif difference == "status":
        statuses = {
            "Status.SUCCESS": py_trees.common.Status.SUCCESS,
            "Status.FAILURE": py_trees.common.Status.FAILURE,
            "Status.RUNNING": py_trees.common.Status.RUNNING,
            "Status.INVALID": py_trees.common.Status.INVALID,
        }
        query = query_manager.make_query(u2.name, "Return", tick=u2.tick, time=u2.time, foils=[statuses[u1.status]])
    elif difference == "action":
        foils = [manager1.state.retrieve_action(u1.action)]
        query = query_manager.make_query(u2.name, "Decision", tick=u2.tick, time=u2.time, foils=foils)
    else:
        raise ValueError(f"Unknown difference {difference}")
    
    # Transform query into string for llm
    qkey = query.foil_vars()[0]
    qvar = node_names[qkey]
    qval = query.foils[qkey][0] # NB: Assumes only one foil, which is valid for this experiment
    rval = u2.action # Assumes action, also valid for this experiment
    #qstring = f"Why({qvar}={rval},{qvar}={qval},tick:{query.tick},time:{query.time})"

    qstring = f"Identify the reasons in the dictionary format why {qvar}={rval} and not {qvar}={qval}, at tick {query.tick} and time {query.time}"
    qstring += f"\n\nAnswer as in these examples:\n{prompt_example_explanations()}"

    # Prompt LLM
    messages = [
        {"role":"system", "content":llm_system_prompt},
        {"role":"user", "content":qstring}
    ]

    start_timer = timeit.default_timer()

    #print(f"System Prompt: {llm_system_prompt}")
    #print(f"User Prompt: {qstring}")
    response = ollama.chat(model=model_name, messages=messages)
    rstring = response.message.content

    # Extract only the dictionary, assuming it is bounded by the first and last []
    start = rstring.find('[')
    end = rstring.rfind(']')
    
    if start == -1 or end == -1 or end < start:
        raise "Uh oh"
    
    json_string = rstring[start:end+1]
    llm_explanations = json.loads(json_string)

    response_timer = timeit.default_timer()
    response_time = response_timer - start_timer
    
    # Calculate metrics

    # Runtime
    print(f"Response time: {response_time}")

    # Number of explanations
    num_exps = len(llm_explanations)
    print(f"Number of Explanations: {num_exps}")

    # Calculate causal explanations for comparison
    explanations,tick,time,num_nodes,num_cfx = comparer.explain_first_difference(
            max_depth=1,
            visualise=False,
            visualise_only_valid=False,
            hide_display=True,
        )
    
    # First, is the target variable recovered?
    target_recovered = False
    for llm_exp in llm_explanations:
        if llm_exp["reason"] == target_var:
            target_recovered = True
            break
    print(f"Target recovered: {target_recovered}")

    # Second, count how many llm explanations are contained in the real explanation set
    num_true_var = 0
    num_true_val = 0
    num_real_vars = 0

    for llm_exp in llm_explanations:
        reason_list = llm_exp["reason"].split("=")
        reason_var = reason_list[0]
        reason_val = reason_list[1]
        
        var_match = False
        val_match = False
        for exp in explanations:
            exp_var_time = list(exp.reason.keys())[0]
            exp_var = node_names[exp_var_time]
            exp_val = exp.reason[exp_var_time]

            if reason_var == exp_var:
                var_match = True
                if reason_val == exp_val:
                    val_match = True

        if var_match:
            num_true_var += 1
        if val_match:
            num_true_val += 1

        # Check if variable was made up
        if reason_var in CognitiveSequenceState.default_values():
            num_real_vars += 1

    metrics = {
        "runtime":response_time,
        "num_exps":num_exps,
        "true_var_score":num_true_var/num_exps,
        "true_val_score":num_true_val/num_exps,
        "real_var_score":num_real_vars/num_exps,
    }


    if not hide_display:
        print(f"Number of times correct variable was identified: {num_true_var}/{num_exps}")
        print(f"Number of times correct variable had correct value: {num_true_val}/{num_exps}")
        print(f"Number of times the reason variable corresponds to a real state variable: {num_real_vars}/{num_exps}")

    return True,metrics
