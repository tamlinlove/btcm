# btcm
Generating causal models of behaviour trees for counterfactual explanations

## Executing Behaviour Trees
To run the serial recall use case, use the following:

```
python cog_seq_test.py -p profile_name
```

replacing *profile_name* with one of *default*, *frustrated*, *no_attention*, *no_memory*, *no_reactivity*. You can also include the *--skip* argument to skip waiting for simulated user responses, and *--display* to show the interaction between the simulated user and robot. Running this script will save the episodic memory as *logs/cognitive_sequence/cog_log_profile_name.json*.

To explain the newly generated execution, run

```
python cog_seq_explain.py -p profile_name
```

replacing *profile_name* with the same profile used to generate the execution. To change the default query, you can pass through the following arguments:

* -n : the name of the node, such as SequenceLength, SequenceComplexity, etc. (state variables),  or DecideSocialAction, SetSequenceParameters, etc. (bt nodes)
* -t : the type of node, either State for state variables, or Return, Executed, Decision for BT nodes
* -i : the tick being queried, by default 0
* -j : the time step being queried, by default "end", which is the last time step of the selected tick
* -v : the foils, as a list of foil values. By default, it is anything except the true value

You can also configure ths search with the following arguments:

* --max_depth : the maximum depth (i.e. number of counterfactual variables) before giving up the search

## Replciating Experiments

The following replicates the random BT experiments:

```
python random_tests.py
python random_explain.py
```

The following replicates the serial recall experiments:

```
./run_multi.sh
./evaluate_cog.sh
```

Some example queries for the case study BT can be executed by running:

```
python run_case_study.py
```

## Code Structure
The *btcm* package is divided into a number of subpackages:

* dm - manages classes relating to basic decision-making, defining states, actions and environments
* bt - manages behaviour tree logic, including the node wrappers that define the execute, decide, etc. functions, loggers for episodic memory, and the state used to reconstruct the BT for making a causal model
* cm - manages the causal model class used to construct models and perform causal operations such as interventions
* cfx - manages a counterfactual explainer used to specify queries and generate explanations
* examples - contains ready-made behaviour trees for testing and evaluation, including the serail recall task (cognitive_sequence), the random BTs and the case study example
