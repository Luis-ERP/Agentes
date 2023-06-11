from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import time, datetime, random
import numpy as np


class VictimAgent(Agent):
    def __init__(self, model):
        super().__init__(random.random(), model)

    def move(self):
        pass

    def exit(self):
        pass

    def step(self):
        self.move()


class RescueAgent(Agent):
    def __init__(self, model, visibility_radio=1):
        super().__init__(random.random(), model)
        self.visibility_radio = visibility_radio
        self.carrying_victim = None 

    def move_towards_exit(self):
        pass

    def is_in_exit_cells(self):
        return bool

    def move_to_next_cell(self):
        pass

    def is_victim_in_cell(self):
        return bool

    def carry_victim(self):
        pass

    def step(self):
        if self.carrying_victim and self.is_in_exit_cells():
            self.carrying_victim.exit()
            self.carrying_victim = None

        elif self.carrying_victim:
            self.move_towards_exit()

        elif self.is_victim_in_cell():
            self.carry_victim()

        else:
            self.move_to_next_cell()

    
class Warehouse(Model):
    WIDTH, HEIGHT = 30, 50
    EXIT_CELLS = [(28,0), (29,0)]
    RESCUERS = 10
    VICTIMS = 50

    def __init__(self):
        self.grid = MultiGrid(self.WIDTH, self.HEIGHT, True)
        self.schedule = RandomActivation(self)
        self.cells = np.zeros((self.WIDTH, self.HEIGHT))
        self.step_counter = 0

        # Place victims
        for _ in range(self.VICTIMS):
            empty_cell = self.grid.find_empty()
            agent = VictimAgent(self)
            self.grid.place_agent(agent, empty_cell)
            self.schedule.add(agent)

        # Place rescuers
        for _ in range(self.RESCUERS):
            agent = RescueAgent(self)
            self.grid.place_agent(agent, self.EXIT_CELLS[-1])
            self.schedule.add(agent)

    def serialize_agents(self):
        data = [
            {
                "agent": "victim",
                "position": [29, 49],
                "display": True,
            }
        ]
        return data
    
    def step(self):
        self.step_counter += 1
        self.schedule.step()
        return self.serialize_agents()

    def run(self):
        start = time.time()
        while len(self.get_people_alive()) > 0:
            self.step()
        end = time.time()
        print(f"Tiempo de ejecución:{end-start}")
        return self.step_counter
    

if __name__ == '__main__':
    model = Warehouse()
    model.run()

"""
***** *** *** *** ***** *** *** *****
"""