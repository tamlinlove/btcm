import networkx as nx
import itertools
import copy

from btcm.cm.causalmodel import CausalModel
from btcm.dm.state import State

from typing import Dict,List

class CounterfactualQuery:
    def __init__(self,foils:Dict[str,list]):
        '''
        foils is a dict mapping the names of variables in the causal model to lists of acceptable values
        '''
        self.foils = foils

    def __str__(self):
        return str(self.foils)
    
    def foil_vars(self):
        return list(self.foils.keys())

    def satisfies_query(self,state:State) -> bool:
        '''
        Returns True if the state satisfies the conditions outlined by the foils provided to the query
        '''
        for var in self.foils:
            if state.vals[var] not in self.foils[var]:
                return False
        return True
    
class CounterfactualExplanation:
    def __init__(self,interventions:dict,counterfactual_foil:dict,state:State):
        self.reason = {node:state.vals[node] for node in interventions}
        self.counterfactual_intervention = interventions
        self.counterfactual_foil = counterfactual_foil
        self.state_vals = copy.deepcopy(state.vals)

    def assignment_string(self,names:dict,values:dict=None):
        if values is None:
            values = names
        text = ""
        val_list = list(names.keys())
        for i in range(len(val_list)):
            node = val_list[i]
            text += f"{node} = {values[node]}"
            if i == len(val_list) - 1:
                continue
            elif i == len(val_list) - 2:
                text += ", and "
            else:
                text += ", "
        return text

    def text(self):
        fact_text = self.assignment_string(self.counterfactual_foil,self.state_vals)
        reason_text = self.assignment_string(self.reason)
        intervention_text = self.assignment_string(self.counterfactual_intervention)
        foil_text = self.assignment_string(self.counterfactual_foil)

        return f"The reason that {fact_text} is because {reason_text}. If instead {intervention_text}, then what would have happened is that {foil_text}."


        


class Explainer:
    def __init__(self,model:CausalModel):
        self.model = model

    '''
    QUERY
    '''
    def construct_query(self,foils:dict[str,list]) -> CounterfactualQuery:
        proper_foil:Dict[str,list] = {}
        for var in foils:
            # First, validate var
            if var not in self.model.state.vars():
                raise ValueError(f"Unrecognised variable {var} in query")
            else:
                # Populate foils with var range if not specified
                if foils[var] is None:
                    proper_foil[var] = copy.deepcopy(self.model.state.ranges()[var])
                else:
                    proper_foil[var] = foils[var]
                
                # Remove real value from possible options
                real_val = self.model.state.vals[var]
                if real_val in proper_foil[var]:
                    proper_foil[var].remove(real_val)
        return CounterfactualQuery(foils=proper_foil)
    
    '''
    SEARCH SPACE
    '''
    def reduce_model(self,query) -> Dict[str,list]:
        # First get the list of possible explanation variables
        ancestors = []
        for node in query.foils:
            ancestors += nx.ancestors(self.model.graph,node)
        ancestors = list(set(ancestors))

        # Next, get all possible values for each
        search_space:Dict[str,list] = {node:copy.deepcopy(self.model.state.ranges()[node]) for node in ancestors}

        # Remove true values from search space
        for node in ancestors:
            search_space[node].remove(self.model.state.vals[node])
        
        return search_space
        
    def generate_combinations(self,search_space, N):
        variable_names = list(search_space.keys())
        combinations = []

        # Generate all combinations of N variable names
        for var_combination in itertools.combinations(variable_names, N):
            # Generate all possible value combinations for the selected variables
            value_combinations = itertools.product(*[search_space[var] for var in var_combination])

            # Create a list of dictionaries representing the changes
            for values in value_combinations:
                change = {var: value for var, value in zip(var_combination, values)}
                combinations.append(change)

        return combinations
   
    '''
    EXPLAIN
    '''
    def explain(self,foils:dict[str,list],max_depth:int = None) -> List[CounterfactualExplanation]:
        query:CounterfactualQuery = self.construct_query(foils)

        # TODO: Double check that foil isn't just the real value

        # Start by constructing a new graph only of ancestors to the node in question
        search_space = self.reduce_model(query)

        if max_depth is None:
            max_depth = len(search_space.keys())
        else:
            max_depth = min(max_depth,len(search_space.keys()))

        for i in range(max_depth):
            self.explain_to_depth(query=query,search_space=search_space,depth=i+1)

    def explain_to_depth(self,query:CounterfactualQuery,search_space:Dict[str,list],depth:int):
        search_combos = self.generate_combinations(search_space=search_space,N=depth)

        explanations = []
        for combo in search_combos:
            new_graph,new_state = self.model.intervene(combo)
            if query.satisfies_query(new_state):
                explanations.append(CounterfactualExplanation(combo,new_state.get_values(query.foil_vars()),self.model.state))

        for exp in explanations:
            print("---",exp.text())
        
        






    