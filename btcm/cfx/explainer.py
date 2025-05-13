import networkx as nx
import itertools
import copy

from btcm.cm.causalmodel import CausalModel
from btcm.dm.state import State

from typing import Dict,List

class CounterfactualQuery:
    def __init__(self,foils:Dict[str,list],tick:int = 0, time:int = "end"):
        '''
        foils is a dict mapping the names of variables in the causal model to lists of acceptable values
        '''
        self.foils = foils
        self.tick = tick
        self.time = time

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
    def __init__(self,interventions:dict,counterfactual_foil:dict,state:State,tick:int,time:int):
        self.reason = {node:state.get_value(node) for node in interventions}
        self.counterfactual_intervention = interventions
        self.counterfactual_foil = counterfactual_foil
        self.state_vals = copy.deepcopy(state.vals)
        self.state = state
        self.tick = tick
        self.time = time

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


class AggregatedCounterfactualExplanation(CounterfactualExplanation):
    def __init__(self,interventions:Dict[str,list],counterfactual_foil:dict,state:State,tick:int,time:int):
        super().__init__(interventions,counterfactual_foil,state,tick,time)

    def text(self,names:dict[str,str]=None):
        if len(self.reason.keys()) == 1:
            fact_text = self.assignment_string(self.counterfactual_foil,self.state_vals,node_names=names)
            reason_text = self.assignment_string(self.reason,node_names=names)
            intervention_text = self.intervention_text(names=names)
            foil_text = self.assignment_string(self.counterfactual_foil,node_names=names)
            
            return f"The reason that {fact_text} is because {reason_text}. If instead {intervention_text}, then what would have happened is that {foil_text}."

        else:
            raise NotImplementedError("Can't handle more than one reason yet")
        
    def intervention_text(self,names:dict[str,str]=None):
        text = ""
        
        for var in self.counterfactual_intervention:
            vals = self.counterfactual_intervention[var]
            real_val = self.reason[var]
            
            if names is not None:
                var_name = names[var]
            else:
                var_name = var

            var_range = self.state.ranges()[var]
            if var_range.range_type == "disc_cont":
                if len(vals) == 1:
                    text += f"{var_name} = {vals[0]}"
                elif self.is_continuous_subset(vals,var_range.values):
                    if vals[0] == var_range.values[0]:
                        text += f"{var_name} <= {vals[-1]}"
                    elif vals[-1] == var_range.values[-1]:
                        text += f"{var_name} >= {vals[0]}"
                    elif real_val > vals[0] and real_val < vals[-1]:
                        text += f"{var_name} is in the set {vals}"
                    else:
                        text += f"{var_name} is in the interval [{vals[0]},{vals[-1]}]"
                else:
                    text += f"{var_name} is in the set {vals}"
            elif var_range.range_type == "bool":
                text += f"{var_name} = {vals[0]}"
            elif var_range.range_type == "cat":
                if len(vals) == 1:
                    text += f"{var_name} = {vals[0]}"
                elif len(vals) == 2:
                    text += f"{var_name} is either {vals[0]} or {vals[1]}"
                else:
                    text += f"{var_name} is in the set {vals}"
            else:
                raise NotImplementedError(f"Can't handle {var_range.range_type} yet")
            
            if var != list(self.counterfactual_intervention.keys())[-1]:
                text += ", "
        
        return text
    
    '''
    UTILITY
    '''
    def is_continuous_subset(self,sub_list, main_list):
        # Check if all elements of sub_list are in main_list
        if not all(elem in main_list for elem in sub_list):
            return False

        # Find the indices of the first and last elements of sub_list in main_list
        first_index = main_list.index(sub_list[0])
        last_index = main_list.index(sub_list[-1])

        # Extract the corresponding segment from main_list
        main_segment = main_list[first_index:last_index + 1]

        # Check if the segment matches the sub_list
        return main_segment == sub_list
        

        


class Explainer:
    def __init__(self,model:CausalModel,node_names:dict[str,str]=None,history:dict=None):
        self.model = model
        self.node_names = node_names
        self.history = history

    '''
    QUERY
    '''
    def construct_query(self,foils:dict[str,list],tick:int = 0, time:int = "end") -> CounterfactualQuery:
        proper_foil:Dict[str,list] = {}
        for var in foils:
            # First, validate var
            if not var in self.model.state.vars():
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
        return CounterfactualQuery(foils=proper_foil,tick=tick,time=time)
    
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
    
    def search_graph(self,query:CounterfactualQuery,search_space:Dict[str,list]):
        allowed_nodes = list(search_space.keys()) + list(query.foils.keys())

        return self.model.graph.subgraph(allowed_nodes)
        
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
    def explain(self,query:CounterfactualQuery,max_depth:int = None, visualise:bool = False, visualise_only_valid:bool =False, visualised_interventions: list = None) -> List[CounterfactualExplanation]:
        # Validate
        for var in query.foils:
            if query.foils[var] is None:
                continue
            for var_val in query.foils[var]:
                if var_val == self.model.state.get_value(var):
                    raise ValueError(f"Cannot construct query with {var} = {var_val} as it is the current value of the variable")

        # Start by constructing a new graph only of ancestors to the node in question
        search_space = self.reduce_model(query)
        search_graph = self.search_graph(query, search_space)

        if max_depth is None:
            max_depth = len(search_space.keys())
        else:
            max_depth = min(max_depth,len(search_space.keys()))

        explanations = []
        for i in range(max_depth):
            new_exps = self.explain_to_depth(query=query,search_space=search_space,depth=i+1,search_graph=search_graph,visualise=visualise,visualise_only_valid=visualise_only_valid,visualised_interventions=visualised_interventions)

            # Aggregate
            new_exps = self.aggregate_explanations(new_exps)

            explanations += new_exps

            if len(explanations) > 0:
                break

        return explanations

    def explain_to_depth(
            self,
            query:CounterfactualQuery,
            search_space:Dict[str,list],
            depth:int,
            search_graph:nx.DiGraph,
            visualise:bool=False,
            visualise_only_valid:bool=False,
            visualised_interventions:list=None
    ):
        search_combos = self.generate_combinations(search_space=search_space,N=depth)

        explanations = []
        for combo in search_combos:
            new_graph,new_state = self.model.intervene(combo,search_graph)
           
            satisfied = False
            if query.satisfies_query(new_state):
                satisfied = True
                explanations.append(CounterfactualExplanation(combo,new_state.get_values(query.foil_vars()),self.model.state,query.tick,query.time))

            if visualise:
                display_this = True

                if visualise_only_valid and not satisfied:
                    display_this = False
                elif visualised_interventions is not None:
                    # Set display_this to false if all variables in combo are not in the visualised interventions
                    one_var_in_intervention_list = False
                    for var in combo:
                        if var in visualised_interventions:
                            one_var_in_intervention_list = True
                            break
                    if not one_var_in_intervention_list:
                        display_this = False
                
                if display_this:
                    self.visualise_intervention(combo,new_graph,new_state,query,search_space)
        
        return explanations
    
    def aggregate_explanations(self,explanations:List[CounterfactualExplanation]):

        # First, group all explanations that share the same variables and foil values
        grouped_explanations = {}
        for exp in explanations:
            var_key = tuple(sorted(exp.reason.keys()))
            foil_key = tuple([str(exp.counterfactual_foil[var]) for var in sorted(exp.counterfactual_foil)])
            if var_key not in grouped_explanations:
                grouped_explanations[var_key] = {foil_key: [exp]}
            else:
                if foil_key not in grouped_explanations[var_key]:
                    grouped_explanations[var_key][foil_key] = [exp]
                else:
                    grouped_explanations[var_key][foil_key].append(exp)

        # Create a new aggregated explanation for each group
        new_explanations = []
        for intervention in grouped_explanations:
            for foil_value in grouped_explanations[intervention]:
                intervention_dict = {}
                for exp in grouped_explanations[intervention][foil_value]:
                    for var in exp.counterfactual_intervention:
                        if var not in intervention_dict:
                            intervention_dict[var] = [exp.counterfactual_intervention[var]]
                        else:
                            intervention_dict[var].append(exp.counterfactual_intervention[var])
                
                foil = grouped_explanations[intervention][foil_value][0].counterfactual_foil
                state = grouped_explanations[intervention][foil_value][0].state
                tick = grouped_explanations[intervention][foil_value][0].tick
                time = grouped_explanations[intervention][foil_value][0].time

                aggregated_exp = AggregatedCounterfactualExplanation(intervention_dict,foil,state,tick,time)
                new_explanations.append(aggregated_exp)

        return new_explanations

    '''
    VISUALISATION
    '''
    def visualise_intervention(self,intervention,new_graph,new_state,query,search_space):
        # Find reduced set of nodes for graph
        reduced_nodes = {node:self.model.nodes[node] for node in self.model.nodes if (node in search_space or node in query.foils)}   

        # Create new label dict
        label_dict = {}
        colours = {}
        for node in reduced_nodes:
            node_id = reduced_nodes[node].name
            original_value = self.model.state.get_value(node_id)
            current_value = new_state.get_value(node_id)
            if node in intervention:
                label_dict[reduced_nodes[node].name] = f"DO: {self.node_names[node]} : {original_value} -> {current_value}"
                colours[reduced_nodes[node].name] = "red"
            else:
                if original_value != current_value:
                    label_dict[reduced_nodes[node].name] = f"{self.node_names[node]} : {original_value} -> {current_value}"
                else:
                    label_dict[reduced_nodes[node].name] = f"{self.node_names[node]} : {current_value}"

                if node in query.foils:
                    colours[reduced_nodes[node].name] = "green"
                else:
                    colours[reduced_nodes[node].name] = "cyan"

        # Visualise
        self.model.visualise(new_graph,new_state,nodes=reduced_nodes,label_dict=label_dict,colours=colours)
        
        






    