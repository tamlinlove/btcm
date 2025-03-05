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
