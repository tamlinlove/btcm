import py_trees

from btcm.cfx.query_manager import QueryManager
from btcm.cfx.explainer import Explainer,AggregatedCounterfactualExplanation
from btcm.bt.btstate import BTStateManager

def display(text,hide_display:bool=False):
    # TODO: Maybe put this in a utility file
    if not hide_display:
        print(text)
    else:
        pass

class Update:
    def __init__(self, name:str, status:str, action:str, tick:int, time:int):
        self.name = name
        self.status = status
        self.action = action
        self.tick = tick
        self.time = time

class Comparer:
    def __init__(self, manager1:BTStateManager, manager2:BTStateManager):
        self.manager1 = manager1
        self.manager2 = manager2

    '''
    FOLLOW-UP
    '''
    def explain_follow_ups(
            self,
            target_var:str,
            max_follow_ups:int=2,
            max_depth:int=1,
            visualise:bool=False,
            visualise_only_valid:bool=False,
            hide_display:bool=False,
    ) -> tuple[bool,int,int]:
        # First round of explanations
        explanations,tick,time = self.explain_first_difference(
            max_depth=max_depth,
            visualise=visualise,
            visualise_only_valid=visualise_only_valid,
            hide_display=hide_display,
        )

        # Check if explanation is valid
        if explanations is None:
            display("No differences",hide_display=hide_display)
            return False,0,0

        # Check if target found
        if target_var is None:
            display("\nNo need for follow-ups\n",hide_display=hide_display)
        elif self.target_found(explanations,target_var):
            display("Found target in 1 step",hide_display=hide_display)
            return True,1,len(explanations)
        else:
            # Need to do follow up queries
            step = 2

            # Reinitialise
            
            explainer = Explainer(self.manager2.model, node_names=self.node_names, history=self.manager2.value_history)
            query_manager = QueryManager(explainer, self.manager2, visualise=visualise, visualise_only_valid=visualise_only_valid)
           

            while step <= max_follow_ups:
                display(f"\n==========\n==========\nROUND {step}\n==========\n==========",hide_display=hide_display)
                next_exps = []
                for explanation in explanations:
                    # Reinitialise
                    self.manager2.load_state(tick=explanation.tick,time=explanation.time)
                    explainer = Explainer(self.manager2.model, node_names=self.node_names, history=self.manager2.value_history)
                    query_manager = QueryManager(explainer, self.manager2, visualise=visualise, visualise_only_valid=visualise_only_valid)

                    # Create query
                    foil = self.foil_from_explanation(explanation)
                    curr_tick = explanation.tick
                    vars = list(foil.keys())
                    if len(list(foil.keys())) == 1:
                        # TODO: Fix to handle multiple 
                        var = vars[0]
                        update_history = self.manager2.update_history[var]
                        curr_tick,curr_time = self.get_curr_time([var],{var:update_history},curr_tick)
                        num_parents = sum(1 for _ in self.manager2.model.graph.predecessors(var))
                    else:
                        update_history = {var:self.manager2.update_history[var] for var in vars}
                        curr_tick,curr_time = self.get_curr_time(vars,update_history,curr_tick)
                        num_parents_list = [sum(1 for _ in self.manager2.model.graph.predecessors(var)) for var in vars]
                        num_parents = max(num_parents_list)

                    # Check if the variable has any parents
                    attempt_explanation = True
                    if num_parents == 0:
                        if curr_tick == 0:
                            #Impossible to go back further
                            display("Cannot attempt explanation")
                            attempt_explanation = False
                        else:
                            # TODO: keep going back until a the chosen variable has parents
                            # Reinitialise to a new tick
                            curr_tick = curr_tick - 1
                            curr_times = []
                            new_foil = {}
                            for var in vars:
                                same_nodes = sorted([node for node in self.manager2.update_history if str(curr_tick) in self.manager2.update_history[node] and self.node_names[node] == self.node_names[var]])
                                last_node = same_nodes[-1]
                                new_foil[last_node] = foil[var]
                                curr_times.append(int(list(self.manager2.update_history[last_node][str(curr_tick)].keys())[-1]))
                            curr_time = max(curr_times)
                            self.manager2.load_state(tick=curr_tick,time=curr_time)
                            explainer = Explainer(self.manager2.model, node_names=self.node_names, history=self.manager2.value_history)
                            query_manager = QueryManager(explainer, self.manager2, visualise=visualise, visualise_only_valid=visualise_only_valid)

                            # Update foil value
                            foil = new_foil
                            

                        
                    if attempt_explanation:
                        # Reinitialise
                        self.manager2.load_state(tick=explanation.tick,time=explanation.time)
                        explainer = Explainer(self.manager2.model, node_names=self.node_names, history=self.manager2.value_history)
                        query_manager = QueryManager(explainer, self.manager2, visualise=visualise, visualise_only_valid=visualise_only_valid)

                        query = query_manager.make_follow_up_query(foil,curr_tick,curr_time)
                        new_explanations = explainer.explain(query, max_depth=max_depth, visualise=visualise, visualise_only_valid=visualise_only_valid)
                        
                        display(f"\n=====QUERY=====\n{query_manager.query_text(query)}", hide_display=hide_display)
                        display("\n=====EXPLANATION=====",hide_display=hide_display)
                        for exp in new_explanations:
                            display(f"-----{exp.text()}",hide_display=hide_display)

                        # Add new explanations to a list of all explanations for this round
                        next_exps += new_explanations

                    
                # Check if target is found
                if self.target_found(next_exps,target_var):
                    display(f"Found target in {step} steps",hide_display=hide_display)
                    return True,step,len(next_exps)
                
                explanations = next_exps
                    

                # Increment
                step += 1

        return False,0,0

        




    '''
    EXPLANATION
    '''
    def explain_first_difference(self,max_depth:int=1,visualise:bool=False,visualise_only_valid:bool=False,hide_display:bool=False):
        # Get the first difference between the two queries
        same, difference, update1, update2 = self.find_first_difference()
        explanations = []

        if same:
            display("No differences found",hide_display=hide_display)
            return None,None,None
        
        # Load the state
        self.manager2.load_state(tick=update2.tick, time=update2.time)
        self.node_names = self.manager2.pretty_node_names()

        # Load the explainer
        explainer = Explainer(self.manager2.model, node_names=self.node_names, history=self.manager2.value_history)

        # Query manager
        query_manager = QueryManager(explainer, self.manager2, visualise=visualise, visualise_only_valid=visualise_only_valid)

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
            query = query_manager.make_query(update2.name, "Return", tick=update2.tick, time=update2.time, foils=[statuses[update1.status]])
        elif difference == "action":
            foils = [self.manager1.state.retrieve_action(update1.action)]
            query = query_manager.make_query(update2.name, "Decision", tick=update2.tick, time=update2.time, foils=foils)
        else:
            raise ValueError(f"Unknown difference {difference}")
        
        explanations = explainer.explain(query, max_depth=max_depth, visualise=visualise, visualise_only_valid=visualise_only_valid)
        display(f"\n=====QUERY=====\n{query_manager.query_text(query)}", hide_display=hide_display)
        display("\n=====EXPLANATION=====",hide_display=hide_display)
        for explanation in explanations:
            display(f"-----{explanation.text(names=self.node_names)}",hide_display=hide_display)
        
        
        return explanations,update2.tick,update2.time
    
    '''
    QUERY
    '''
    def target_found(self,explanations:list[AggregatedCounterfactualExplanation],target:str):
        # TODO: Make sure this works for multiple foils
        target_found = False
        for explanation in explanations:
            for var in explanation.counterfactual_intervention:
                var_name = self.node_names[var]
                if var_name == target:
                    target_found = True
                    break
            if target_found:
                break

        return target_found
    
    def foil_from_explanation(self,explanation:AggregatedCounterfactualExplanation):
        # TODO: Add previous foil???
        # TODO: Handle explanations with multiple intervention variables
        
        # Foil
        return explanation.counterfactual_intervention


    '''
    COMPARISON
    '''
    def find_first_difference(self,difference_type=None):
        # TODO: Maybe difference type should be in a different function that looks at updates of a particular type regardless of the tick and time
        data1 = self.manager1.data
        data2 = self.manager2.data

        tick = 0
        time = 1
        stop = False

        same = True
        difference = None
        u1 = None
        u2 = None

        while not stop:
            if str(tick) not in data1.keys() or str(tick) not in data2.keys():
                break

            while True:
                if str(time) not in data1[str(tick)].keys() or str(time) not in data2[str(tick)].keys():
                    if str(time) in data1[str(tick)].keys():
                        print(f"Tick {tick} time {time} not in data2")
                    elif str(time) in data2[str(tick)].keys():
                        print(f"Tick {tick} time {time} not in data1")
                    break

                update1 = data1[str(tick)][str(time)]["update"]
                update2 = data2[str(tick)][str(time)]["update"]

                same,difference,contents1,contents2 = self.compare_updates(update1,update2)

                stop = False
                if difference_type is not None:
                    if difference == difference_type:
                        stop = True
                else:
                    if not same:
                        stop = True

                if stop:
                    u1 = Update(contents1["name"],contents1["status"],contents1["action"],tick,time)
                    u2 = Update(contents2["name"],contents2["status"],contents2["action"],tick,time)
                    break

                # Update
                time += 1
            if not stop:
                tick += 1

        return same,difference,u1,u2

    def compare_updates(self,update1,update2):
        # Compare the updates
        contents1 = update1[list(update1.keys())[0]]
        contents2 = update2[list(update2.keys())[0]]
        
        for comparison_point in ["name","status","action"]:
            if comparison_point in contents1.keys() and comparison_point in contents2.keys():
                if contents1[comparison_point] != contents2[comparison_point]:
                    return False,comparison_point,contents1,contents2
                
        return True,None,None,None
    
    '''
    UTILITY
    '''
    def get_curr_time(self,vars,update_history,curr_tick):
        times = []
        for var in vars:
            if str(curr_tick) not in update_history[var]:
                curr_tick = max([int(key) for key in update_history[var]])
                
            times.append(int(list(update_history[var][str(curr_tick)].keys())[-1]))
            
        curr_time = max(times)
        return curr_tick,curr_time