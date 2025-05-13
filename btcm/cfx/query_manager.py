import py_trees

from btcm.cfx.explainer import Explainer,CounterfactualQuery
from btcm.bt.btstate import BTStateManager,BTState
from btcm.bt.nodes import ActionNode

# TODO: Add different query makers (e.g. all except null for actions, etc.)

class QueryManager:
    def __init__(self,explainer:Explainer,state_manager:BTStateManager,visualise:bool=False, visualise_only_valid:bool=False):
        self.explainer = explainer
        self.manager = state_manager
        self.visualise = visualise
        self.visualise_only_valid = visualise_only_valid

    '''
    QUERIES
    '''
    def make_query(self,name:str,nodetype:str,tick=0,time="end",foils:list=None) -> CounterfactualQuery:
        '''
        Given a node's name and type, as well as the tick and time to refernce, and a list of foils, create a query object to pass to the explainer

        Note: Manager should already be loaded with the state at the time of the query
        '''
        if time == "end":
            time = sorted(int(key) for key in self.manager.data[str(tick)].keys())[-1]

        if nodetype == "State":
            var_name = self.manager.get_var_name_for_time(name,tick,time)
            q_foil = {var_name:foils}
        else:
            # BT Node
            node_id = self.manager.get_node_from_name(name,nodetype)
            q_foil = {node_id:foils}

        return self.explainer.construct_query(q_foil,tick=tick,time=time)
    
    def make_follow_up_query(self,foil:dict[str,list],tick:int,time:int):
        return CounterfactualQuery(foil,tick,time)
    
    '''
    DISPLAY
    '''
    def query_text(self,query:CounterfactualQuery) -> str:
        '''
        Given a query object, return a natural language string representation of the query
        '''
        if len(query.foil_vars()) > 1:
            # Currently only supports one foil var
            return str(query)
        else:
            if query.tick is not None:
                timestep_text = f" at timestep {query.tick}:{query.time}"
            else:
                timestep_text = ""

            var = query.foil_vars()[0]
            node_category = self.manager.state.categories[var]
            if node_category == "State":
                value_text = f"does {self.manager.state.node_names[var]} = {self.manager.state.get_value(var)}{timestep_text}"
                if query.foils[var] is not None:
                    if len(query.foils[var]) > 1:
                        foil_text = f"one of {query.foils[var]}"
                    else:
                        foil_text = f"{query.foils[var][0]}"
                else:
                    foil_text = "anything else"
            elif node_category == "Return":
                node_name = self.manager.state.behaviour_dict[self.manager.state.nodes[var]].name
                value = self.manager.state.get_value(var)
                status_texts = {
                    py_trees.common.Status.SUCCESS: "success",
                    py_trees.common.Status.FAILURE: "failure",
                    py_trees.common.Status.RUNNING: "running",
                    py_trees.common.Status.INVALID: "an invalid status",
                }
                value_text = f"does node {node_name} return {status_texts[value]}{timestep_text}"
                if len(query.foils[var]) > 1:
                    foil_var_statuses = [status_texts[status] for status in query.foils[var]]
                    foil_text = f"return one of {foil_var_statuses}"
                else:
                    foil_text = f"return {status_texts[query.foils[var][0]]}"
            elif node_category == "Executed":
                node_name = self.manager.state.behaviour_dict[self.manager.state.nodes[var]].name
                value = self.manager.state.get_value(var)
                if value:
                    value_text = f"had node {node_name} been executed{timestep_text}"
                else:
                    value_text = f"had node {node_name} not been executed{timestep_text}"

                return f"Why {value_text}?"
            elif node_category == "Decision":
                behaviour = self.manager.state.behaviour_dict[self.manager.state.nodes[var]]
                node_name = behaviour.name
                if not isinstance(behaviour, ActionNode):
                    raise ValueError(f"Node {node_name} is not an ActionNode, cannot query decision")
                
                value = self.manager.state.get_value(var)
                value_text = f"had node {node_name} selected decision {value}{timestep_text}"

                if len(query.foils[var]) > 1:
                    action_list = [str(action) for action in query.foils[var]]
                    foil_text = f"one of {action_list}"
                else:
                    foil_text = f"{query.foils[var][0]}"
            else:
                raise NotImplementedError(f"Node category {node_category} not implemented")
            
            return f"Why {value_text} and not {foil_text}?"
                

        

        

        

    