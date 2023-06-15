from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
import random
import numpy as np


def get_random_element(numbers, key_func):
    # Calculate the weights for each number
    weights = [1 / key_func(num) if key_func(num) != 0 else 1 for num in numbers]
    # Normalize the weights to sum up to 1
    total_weight = sum(weights)
    normalized_weights = [weight / total_weight for weight in weights]
    indices = range(len(numbers))
    # Use random.choices to select a random element based on the weights
    random_element = random.choices(indices, weights=normalized_weights)[0]
    
    return numbers[random_element]


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
            x, y = self.pos
            self.model.cells[y][x] += 1

            if victim:
                victim.follow = self
                self.mode = "guiding"
            else:
                close_victims = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False,
                                                      radius=self.visibility_radio)
                close_victims = list(filter(lambda agent: agent.type=="victim" and agent.follow==None, close_victims))

                if close_victims:
                    cells = [agent.pos for agent in close_victims] 
                else:
                    cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
                
                # Get the most visited cells and pick a random weighted from from least visite to most
                cells_heat_map = [ self.model.cells[n][m] for m, n in cells ]
                cell_choices = list(zip(cells_heat_map, cells))
                cell_choices.sort(key=lambda c: c[0])
                new_position = get_random_element(cell_choices, lambda c: c[0])[1]

                self.model.grid.move_agent(self, new_position)

        elif self.mode == "guiding" and not self.in_exit():
            new_x, new_y = self.pos
            if self.pos[0] < self.model.WIDTH-1: # X
                new_x += 1
            if self.pos[1] < self.model.HEIGHT-1: # Y
                new_y += 1
            self.model.grid.move_agent(self, (new_x, new_y))
            
        elif self.mode == "guiding" and self.in_exit():
            self.mode = "searching"
    

class Warehouse(Model):
    WIDTH, HEIGHT = 50, 30
    EXIT_CELLS =  [(WIDTH-2, HEIGHT-1), (WIDTH-1, HEIGHT-1)]
    RESCUERS = 10
    VICTIMS = 25

    def __init__(self):
        self.grid = MultiGrid(self.WIDTH, self.HEIGHT, torus=False)
        self.cells = np.zeros((self.HEIGHT, self.WIDTH))
        self.cells[0][0] = 1
        self.schedule = RandomActivation(self)

        # Place victim agents
        for _ in range(self.VICTIMS):
            empty_cell = self.grid.find_empty()
            agent = VictimAgent(self)
            self.grid.place_agent(agent, empty_cell)
            self.schedule.add(agent)

        # Place rescuer agents
        for i in range(self.RESCUERS):
            visibility = 1 if i > 2 else 2
            agent = RescueAgent(self, visibility_radio=visibility)
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
                "posX": agent.pos[0],
                "posY": -1 * agent.pos[1],
                "type": agent.type
            }
            serialized_agents.append(serialized_agent)
        return serialized_agents
    
    def convert_to_plot_matrix(self):
        matrix = [[0 for m in range(self.WIDTH)] for n in range(self.HEIGHT)]
        # Color the historical steps
        for n in range(len(self.cells)):
            for m in range(len(self.cells[n])):
                matrix[n][m] = self.cells[n][m]

        # Color the exit points
        for m, n in self.EXIT_CELLS:
            matrix[n][m] = -1
        
        # Color the agents
        for agents, m, n in self.grid.coord_iter():
            for agent in agents:
                x, y = agent.pos
                if agent.type == 'victim':
                    matrix[y][x] = -2
                elif agent.type == 'rescuer':
                    if agent.mode == 'searching':
                        matrix[y][x] = -3
                    elif agent.mode == 'guiding':
                        matrix[y][x] = -4
        
        return matrix

    def animate(self):
        matrix = np.array(self.convert_to_plot_matrix())
        # Define colormap
        colors = ['gray', 'black', 'blue', 'red', 'white']
        green_colormap = mpl.colormaps['Greens']
        cmap_list = []
        # Add colors for values -4 to 0
        for color in colors:
            cmap_list.append(mcolors.to_rgba(color))
        
        # Add colors for values 1 to 255 using the sequential greens colormap
        bounds = [-4.5, -3.5, -2.5, -1.5, -0.5, 0.5]
        counter = 1
        for i in range(1, 256, 25):
            rgba = green_colormap(i)
            cmap_list.append((rgba[0], rgba[1], rgba[2], rgba[3]))
            bounds.append(counter * 1.5)
            counter += 1
        
        custom_cmap = mcolors.ListedColormap(cmap_list)
        norm = plt.cm.colors.BoundaryNorm(bounds, custom_cmap.N)

        # Plot the grid
        plt.imshow(matrix, cmap=custom_cmap, norm=norm, interpolation='none')
        plt.grid(True, which='both', color='black', linewidth=0.5)
        plt.xticks(np.arange(0, matrix.shape[1], 1)-0.5)
        plt.yticks(np.arange(0, matrix.shape[0], 1)-0.5)
        plt.pause(0.7)

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
    