from btcm.cfx.explainer import Explainer,CounterfactualQuery
from btcm.bt.btstate import BTStateManager,BTState

# TODO: Add different query makers (e.g. all except null for actions, etc.)

class QueryManager:
    def __init__(self,explainer:Explainer,state_manager:BTStateManager,visualise:bool=False):
        self.explainer = explainer
        self.manager = state_manager

    '''
    QUERIES
    '''
    def make_query(self,name:str,nodetype:str,tick=0,time="end",foils:list=None) -> CounterfactualQuery:
        '''
        Given a node's name and type, as well as the tick and time to refernce, and a list of foils, create a query object to pass to the explainer

        Note: Manager should already be loaded with the state at the time of the query
        '''
        if nodetype == "State":
            var_name = self.manager.get_var_name_for_time(name,tick,time)
            q_foil = {var_name:foils}
        else:
            # BT Node
            node_id = self.manager.get_node_from_name(name,nodetype)
            q_foil = {node_id:foils}

        return self.explainer.construct_query(q_foil)

        

        

    