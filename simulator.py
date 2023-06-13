from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import numpy as np

class VictimAgent(Agent):
    def __init__(self, model):
        super().__init__(random.random(), model)
        self.follow : RescueAgent = None
        self.type = "victim"
        self.rescued = False

    def in_exit(self):
        return self.pos in self.model.EXIT_CELLS

    def step(self):
        if self.rescued:
            return 
        
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = random.choice(possible_steps)

        if self.follow is not None:
            new_position = self.follow.pos
        
        if self.in_exit():
            self.model.grid.remove_agent(self)
            self.rescued = True
        else:
            self.model.grid.move_agent(self, new_position)


class RescueAgent(Agent):
    def __init__(self, model, visibility_radio=1):
        super().__init__(random.random(), model)
        self.visibility_radio = visibility_radio
        self.type = "rescuer"
        self.mode = "searching"

    def is_victim_at_current_position(self):
        victim_agents = self.model.grid.get_cell_list_contents([self.pos])
        for agent in victim_agents:
            if agent.type == "victim":
                return agent
        return None

    def in_exit(self):
        return self.pos in self.model.EXIT_CELLS

    def step(self):
        victim = self.is_victim_at_current_position()
        if self.mode == "searching":
            if victim:
                victim.follow = self
                self.mode = "guiding"
            else:
                empty_cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
                new_position = random.choice(empty_cells)
                self.model.grid.move_agent(self, new_position)

        elif self.mode == "guiding" and not self.in_exit():
            new_x, new_y = self.pos
            if self.pos[0] < len(self.model.grid[0])-1:
                new_x += 1
            if self.pos[1] > 0:
                new_y -= 1
            self.model.grid.move_agent(self, (new_x, new_y))
            
        elif self.mode == "guiding" and self.in_exit():
            self.mode = "searching"
    

class Warehouse(Model):
    WIDTH, HEIGHT = 30, 50
    EXIT_CELLS =  [(28,0), (29,0)] #[(4,0), (3,0)] #
    RESCUERS = 10
    VICTIMS = 50

    def __init__(self):
        self.grid = MultiGrid(self.WIDTH, self.HEIGHT, torus=False)
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
            if agent.type == "victim" and agent.rescued:
                continue
            serialized_agent = {
                "id": agent.unique_id,
                "position": list(agent.pos),
                "type": agent.type
            }
            serialized_agents.append(serialized_agent)
        return serialized_agents
    
    def convert_to_plot_matrix(self):
        matrix = [[0 for m in range(self.WIDTH)] for n in range(self.HEIGHT)]
        for m, n in self.EXIT_CELLS:
            matrix[n][m] = 2

        for agents, m, n in self.grid.coord_iter():
            for agent in agents:
                x, y = agent.pos
                if agent.type == 'victim':
                    matrix[y][x] = -1
                elif agent.type == 'rescuer':
                    if agent.mode == 'guiding':
                        matrix[y][x] = 3
                    else:
                        matrix[y][x] = 1
        
        return matrix

    def animate(self):
        matrix = np.array(self.convert_to_plot_matrix())
        # Define colormap
        cmap = plt.cm.colors.ListedColormap(['blue', 'white', 'black', 'red', 'gray'])
        bounds = [-1.5, -0.5, 0.5, 1.5, 2.5, 3.5]  # Bounds for each color
        norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

        # Plot the grid
        plt.imshow(matrix, cmap=cmap, norm=norm, interpolation='none')
        plt.grid(True, which='both', color='black', linewidth=0.5)
        plt.xticks(np.arange(0, matrix.shape[1], 1)-0.5)
        plt.yticks(np.arange(0, matrix.shape[0], 1)-0.5)
        plt.pause(0.2)


    def step(self) -> list:
        self.schedule.step()
        return self.serialize_agents()

    def run(self):
        for _ in range(100):
            self.step()
            self.animate()
        plt.show()
    

if __name__ == '__main__':
    model = Warehouse()
    model.run()
    