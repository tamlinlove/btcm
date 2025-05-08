import py_trees

from btcm.cfx.query_manager import QueryManager
from btcm.cfx.explainer import Explainer
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
    QUERY
    '''
    def explain_first_difference(self,max_depth:int=1,visualise:bool=False,visualise_only_valid:bool=False,hide_display:bool=False):
        # Get the first difference between the two queries
        same, difference, update1, update2 = self.find_first_difference()

        if same:
            print("No differences found")
            return None
        
        # Load the state
        self.manager2.load_state(tick=update2.tick, time=update2.time)

        # Load the explainer
        explainer = Explainer(self.manager2.model, node_names=self.manager2.node_names)

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
            display(f"\n=====QUERY=====\n{query_manager.query_text(query)}", hide_display=hide_display)
            display("\n=====EXPLANATION=====",hide_display=hide_display)
            explainer.explain(query, max_depth=max_depth, visualise=visualise, visualise_only_valid=visualise_only_valid)

        elif difference == "action":
            foils = [self.manager1.state.retrieve_action(update1.action)]
            query = query_manager.make_query(update2.name, "Decision", tick=update2.tick, time=update2.time, foils=foils)
            display(f"\n=====QUERY=====\n{query_manager.query_text(query)}", hide_display=hide_display)
            display("\n=====EXPLANATION=====",hide_display=hide_display)
            explainer.explain(query, max_depth=max_depth, visualise=visualise, visualise_only_valid=visualise_only_valid)
        else:
            raise ValueError(f"Unknown difference {difference}")

    '''
    COMPARISON
    '''
    def find_first_difference(self):
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
                if not same:
                    stop = True
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