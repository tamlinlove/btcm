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
    ):
        # First round of explanations
        explanations,tick,time = self.explain_first_difference(
            max_depth=max_depth,
            visualise=visualise,
            visualise_only_valid=visualise_only_valid,
            hide_display=hide_display,
        )

        # Check if target found
        if target_var is None:
            print("\nNo need for follow-ups\n")
        elif self.target_found(explanations,target_var):
            print("\nTarget found in 1 step\n")
        else:
            # Need to do follow up queries
            step = 1

            # Reinitialise
            explainer = Explainer(self.manager2.model, node_names=self.node_names, history=self.manager2.value_history)
            query_manager = QueryManager(explainer, self.manager2, visualise=visualise, visualise_only_valid=visualise_only_valid)

            while step < max_follow_ups:
                display(f"\n==========\n==========\nROUND {step+1}\n==========\n==========")

                for explanation in explanations:
                    # Reinitialise
                    self.manager2.load_state(tick=explanation.tick,time=explanation.time)
                    explainer = Explainer(self.manager2.model, node_names=self.node_names, history=self.manager2.value_history)
                    query_manager = QueryManager(explainer, self.manager2, visualise=visualise, visualise_only_valid=visualise_only_valid)


                    # Create query
                    foil = self.foil_from_explanation(explanation)
                    if len(list(foil.keys())) == 1:
                        var = list(foil.keys())[0]
                        update_history = self.manager2.update_history[var]
                        curr_tick = explanation.tick
                        curr_time = list(update_history[str(curr_tick)].keys())[-1]
                    else:
                        raise NotImplementedError("Can't handle multiple foils yet!")
                    
                    # Check if the variable has any parents
                    num_parents = sum(1 for _ in self.manager2.model.graph.predecessors(var))
                    attempt_explanation = True
                    if num_parents == 0:
                        if curr_tick == 0:
                            #Impossible to go back further
                            attempt_explanation = False
                        else:
                            # TODO: keep going back until a the chosen variable has parents
                            # Reinitialise to a new tick
                            curr_tick = curr_tick - 1
                            same_nodes = sorted([node for node in self.manager2.update_history if str(curr_tick) in self.manager2.update_history[node] and self.node_names[node] == self.node_names[var]])
                            last_node = same_nodes[-1]
                            
                            curr_time = int(list(self.manager2.update_history[last_node][str(curr_tick)].keys())[-1])
                            self.manager2.load_state(tick=curr_tick,time="end")
                            explainer = Explainer(self.manager2.model, node_names=self.node_names, history=self.manager2.value_history)
                            query_manager = QueryManager(explainer, self.manager2, visualise=visualise, visualise_only_valid=visualise_only_valid)

                            # Update foil value
                            foil = {last_node:foil[var]}

                        
                    if attempt_explanation:
                        query = query_manager.make_follow_up_query(foil,curr_tick,curr_time)
                        new_explanations = explainer.explain(query, max_depth=max_depth, visualise=visualise, visualise_only_valid=visualise_only_valid)
                        
                        display(f"\n=====QUERY=====\n{query_manager.query_text(query)}", hide_display=hide_display)
                        display("\n=====EXPLANATION=====",hide_display=hide_display)
                        for exp in new_explanations:
                            print(f"-----{exp.text()}")

                        # Add new explanations to a list of all explanations for this round
                        # TODO

                    
                # Check if target is found
                # TODO
                    

                # Increment
                step += 1

        




    '''
    EXPLANATION
    '''
    def explain_first_difference(self,max_depth:int=1,visualise:bool=False,visualise_only_valid:bool=False,hide_display:bool=False):
        # Get the first difference between the two queries
        same, difference, update1, update2 = self.find_first_difference()
        explanations = []

        if same:
            print("No differences found")
            return None
        
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
            print(f"-----{explanation.text(names=self.node_names)}")
            #print(f"-----{explanation.text(names=None)}")
        
        
        return explanations,update2.tick,update2.time
    
    '''
    QUERY
    '''
    def target_found(self,explanations:list[AggregatedCounterfactualExplanation],target:str):
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

        # Validation
        if len(list(explanation.counterfactual_intervention.keys())) != 1:
            raise NotImplementedError("Can't handle explanations with more than 1 variable yet!!!")
        
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