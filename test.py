import numpy as np

for i in [3.4159999999999995,3.548]:
    rng = np.random.default_rng(597991390)
    n = rng.normal(i,1)
    print(i,n)
