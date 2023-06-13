from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import time, random

class VictimAgent(Agent):
    def __init__(self, model):
        super().__init__(random.random(), model)
        self.follow : RescueAgent = None
        self.type = "victim"
        self.rescued = False

    def step(self):
        if self.rescued:
            return 
        
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = random.choice(possible_steps)

        if self.follow is not None:
            new_position = self.follow.pos
            if self.pos == self.model.EXIT_CELLS[0] or self.pos == self.model.EXIT_CELLS[1]:
                # self.model.grid.remove_agent(self)
                # self.model.schedule.remove(self)
                self.rescued = True

        self.model.grid.move_agent(self, new_position)


class RescueAgent(Agent):
    def __init__(self, model, visibility_radio=1):
        super().__init__(random.random(), model)
        self.visibility_radio = visibility_radio
        self.type = "rescuer"

    def step(self):
        victim_agents = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False,
                                                      radius=self.visibility_radio)
        if victim_agents:
            victim_agents.sort(key=lambda agent: agent.pos, reverse=True)
            victim = victim_agents[0]
            self.model.grid.move_agent(victim, self.model.EXIT_CELLS[-1])
            victim.follow = self
        else:
            empty_cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
            new_position = random.choice(empty_cells)
            self.model.grid.move_agent(self, new_position)
    

class Warehouse(Model):
    WIDTH, HEIGHT = 30, 50
    EXIT_CELLS = [(28,0), (29,0)]
    RESCUERS = 10
    VICTIMS = 50

    def __init__(self):
        self.grid = MultiGrid(self.WIDTH, self.HEIGHT, True)
        self.schedule = RandomActivation(self)

        # Place victim agents
        for _ in range(self.VICTIMS):
            empty_cell = self.grid.find_empty()
            agent = VictimAgent(self)
            self.grid.place_agent(agent, empty_cell)
            self.schedule.add(agent)

        # Place rescuer agents
        for _ in range(self.RESCUERS):
            agent = RescueAgent(self)
            self.grid.place_agent(agent, self.EXIT_CELLS[-1])
            self.schedule.add(agent)

    def serialize_agents(self) -> list:
        agents = self.schedule.agents
        serialized_agents = []
        for agent in agents:
            serialized_agent = {
                "id": agent.unique_id,
                "position": list(agent.pos),
                "type": agent.type
            }
            serialized_agents.append(serialized_agent)
        return serialized_agents
    
    def step(self) -> list:
        self.schedule.step()
        return self.serialize_agents()

    def run(self):
        for _ in range(100):
            self.step()
    

if __name__ == '__main__':
    model = Warehouse()
    model.run()
