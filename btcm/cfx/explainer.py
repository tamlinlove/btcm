import networkx as nx
import itertools
import copy

from btcm.cm.causalmodel import CausalModel
from btcm.dm.state import State,VarRange

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
            if state.get_value(var) not in self.foils[var]: 
                return False
        return True
    
class CounterfactualExplanation:
    def __init__(self,interventions:dict,counterfactual_foil:dict,state:State):
        self.reason = {node:state.get_value(node) for node in interventions}
        self.counterfactual_intervention = interventions
        self.counterfactual_foil = counterfactual_foil
        self.state_vals = copy.deepcopy(state.vals)

    def assignment_string(self,names:dict,values:dict=None,node_names:dict[str,str]=None):
        if values is None:
            values = names
        text = ""
        val_list = list(names.keys())
        for i in range(len(val_list)):
            node = val_list[i]
            if node_names is not None:
                node_name = node_names[node]
            else:
                node_name = node
            text += f"{node_name} = {values[node]}"
            if i == len(val_list) - 1:
                continue
            elif i == len(val_list) - 2:
                if len(val_list) > 2:
                    text += ", and "
                else:
                    text += " and "
            else:
                text += ", "
        return text

    def text(self,names:dict[str,str]=None):
        fact_text = self.assignment_string(self.counterfactual_foil,self.state_vals,node_names=names)
        reason_text = self.assignment_string(self.reason,node_names=names)
        intervention_text = self.assignment_string(self.counterfactual_intervention,node_names=names)
        foil_text = self.assignment_string(self.counterfactual_foil,node_names=names)

        return f"The reason that {fact_text} is because {reason_text}. If instead {intervention_text}, then what would have happened is that {foil_text}."


        


class Explainer:
    def __init__(self,model:CausalModel,node_names:dict[str,str]=None):
        self.model = model
        self.node_names = node_names

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
                # Obtain foils
                var_range = self.model.state.ranges()[var]

                if foils[var] is not None:
                    # Can just use the provided foils, if they are valid
                    for val in foils[var]:
                        if not var_range.valid(val):
                            raise ValueError(f"Invalid foil {val} for variable {var}")
                        proper_foil[var] = foils[var]
                else:
                    if var_range.values is None:
                        raise TypeError(f"Invalid var range of type {var_range.var_type} for variable {var}")
                    proper_foil[var] = copy.deepcopy(var_range.values)
                
                # Remove real value from possible options
                real_val = self.model.state.get_value(var)
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

        # Remove variables that shouldn't be intervened on
        potential_variables = [node for node in ancestors if self.model.state.can_intervene(node)]

        # Next, get all possible values for each
        search_space:Dict[str,list] = {}
        for node in potential_variables:
            values = self.model.state.ranges()[node].values
            if values is None:
                raise TypeError(f"Invalid: var range of type {self.model.state.ranges()[node].range_type} has no values for variable {node}")
            search_space[node] = copy.deepcopy(values)

        # Remove true values from search space
        for node in potential_variables:
            real_val = self.model.state.get_value(node)
            # Check if real val is in the space (it may not be due to discretisation)
            if real_val in search_space[node]:
                search_space[node].remove(self.model.state.get_value(node)) 
        
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
    def explain(self,foils:dict[str,list],max_depth:int = None, visualise:bool = False) -> List[CounterfactualExplanation]:
        query:CounterfactualQuery = self.construct_query(foils)

        # TODO: Double check that foil isn't just the real value

        # Start by constructing a new graph only of ancestors to the node in question
        search_space = self.reduce_model(query)

        if max_depth is None:
            max_depth = len(search_space.keys())
        else:
            max_depth = min(max_depth,len(search_space.keys()))

        for i in range(max_depth):
            self.explain_to_depth(query=query,search_space=search_space,depth=i+1,visualise=visualise)

    def explain_to_depth(self,query:CounterfactualQuery,search_space:Dict[str,list],depth:int,visualise:bool=False):
        search_combos = self.generate_combinations(search_space=search_space,N=depth)

        explanations = []
        for combo in search_combos:
            
            new_graph,new_state = self.model.intervene(combo)
            
            if query.satisfies_query(new_state):
                explanations.append(CounterfactualExplanation(combo,new_state.get_values(query.foil_vars()),self.model.state))

            if visualise:
                self.visualise_intervention(combo,new_graph,new_state,query,search_space)

        for exp in explanations:
            print("---",exp.text(names=self.node_names))

    '''
    VISUALISATION
    '''
    def visualise_intervention(self,intervention,new_graph,new_state,query,search_space):
        # Find reduced set of nodes for graph
        reduced_nodes = {node:self.model.nodes[node] for node in self.model.nodes if (node in search_space or node in query.foils)}       

        # Create new label dict
        label_dict = {}
        colours = []
        for node in reduced_nodes:
            node_id = reduced_nodes[node].name
            original_value = self.model.state.get_value(node_id)
            current_value = new_state.get_value(node_id)
            if node in intervention:
                label_dict[reduced_nodes[node].name] = f"DO: {self.node_names[node]} : {original_value} -> {current_value}"
                colours.append("red")
            else:
                if original_value != current_value:
                    label_dict[reduced_nodes[node].name] = f"{self.node_names[node]} : {original_value} -> {current_value}"
                else:
                    label_dict[reduced_nodes[node].name] = f"{self.node_names[node]} : {current_value}"

                if node in query.foils:
                    colours.append("green")
                else:
                    colours.append("cyan")

        # Visualise
        self.model.visualise(new_graph,new_state,nodes=reduced_nodes,label_dict=label_dict,colours=colours)
        
        






    