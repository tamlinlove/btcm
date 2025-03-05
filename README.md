# btcm
Integrating Behaviour Trees and Causal Models for Explainability in Human-Robot Interaction

## Simple example
You can run the following to execute the behaviour tree and log it into *log.json*:
```
python test.py
```

Then you can run the following to read the log file and reconstruct the BT with a causal model in order to generate explanations:
```
python explain_test.py
```

## Code Structure
The *btcm* package is divided into a number of subpackages:

* dm - manages classes relating to basic decision-making, defining states, actions and environments
* bt - manages behaviour tree logic, including the node wrappers that define the execute, decide, etc. functions, loggers for episodic memory, and the state used to reconstruct the BT for making a causal model
* cm - manages the causal model class used to construct models and perform causal operations such as interventions
* cfx - manages a counterfactual explainer used to specify queries and generate explanations
* examples - contains ready-made behaviour trees for testing. At the moment, just has a toy example of a sequence node with 2 children
