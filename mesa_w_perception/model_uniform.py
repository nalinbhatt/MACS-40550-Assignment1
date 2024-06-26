import mesa
import numpy as np


def calc_similarity(model):
    neighbor_sim = [agent.similar for agent in model.schedule.agents]
    N = model.density*model.width*model.height
    return sum(neighbor_sim) / (N)

class SchellingAgent(mesa.Agent):
    """
    Schelling segregation agent
    """

    def __init__(self, unique_id, model, agent_type, homophily, similar, accepted_dissimilar):
        """
        Create a new Schelling agent.

        Args:
           unique_id: Unique identifier for the agent.
           x, y: Agent initial location.
           agent_type: Indicator for the agent's type (minority=1, majority=0)
        """
        super().__init__(unique_id, model)
        self.type = agent_type
        self.homophily = homophily
        self.similar = similar
        self.accepted_dissimilar = accepted_dissimilar
        self.perceived_similar = self.similar + self.accepted_dissimilar
        

    def step(self):
        
        self.similar = 0
        self.accepted_dissimilar = 0
        for neighbor in self.model.grid.iter_neighbors(
            self.pos, moore=True, radius=self.model.radius
        ):
            if neighbor.type == self.type:
                self.similar += 1

            else:
                preference = self.model.preference
                self.accepted_dissimilar += preference*(1/self.homophily)*1


        # If unhappy, move:
        if self.similar + self.accepted_dissimilar < self.homophily:
            self.model.grid.move_to_empty(self)
        else:
            self.model.happy += 1


class Schelling(mesa.Model):
    """
    Model class for the Schelling segregation model.
    """

    def __init__(
        self,
        height=20,
        width=20,
        homophily_lb=0,
        homophily_ub=1,
        preference=0,
        radius=1,
        density=0.8,
        minority_pc=0.2,
        seed=None,
    ):
        """
        Create a new Schelling model.

        Args:
            width, height: Size of the space.
            density: Initial Chance for a cell to populated
            minority_pc: Chances for an agent to be in minority class
            homophily: Minimum number of agents of same class needed to be happy
            radius: Search radius for checking similarity
            seed: Seed for Reproducibility
        """

        super().__init__(seed=seed)
        self.height = height
        self.width = width
        self.density = density
        self.minority_pc = minority_pc
        self.homophily_ub = homophily_ub
        self.homophily_lb = homophily_lb
        self.radius = radius
        self.preference = preference

        self.schedule = mesa.time.RandomActivation(self)
        self.grid = mesa.space.SingleGrid(width, height, torus=True)

        self.happy = 0
        self.similarity = 0
        self.datacollector = mesa.DataCollector(
            model_reporters={"happy": "happy", "Avg Similarity": "similarity"},
            agent_reporters={"Number of Similar Neighbors": "similar",
            "Perceived Number of Similar Neighbors": "perceived_similar", 
            "Agent type": "type"}  # Model-level count of happy agents
        )

        # Set up agents
        # We use a grid iterator that returns
        # the coordinates of a cell as well as
        # its contents. (coord_iter)
        for _, pos in self.grid.coord_iter():
            if self.random.random() < self.density:
                agent_type = 1 if self.random.random() < self.minority_pc else 0
                np.random.seed(self.next_id())
                homophily = np.random.uniform(homophily_lb, homophily_ub)
                agent = SchellingAgent(self.next_id(), self, agent_type, homophily,0, 0)
                self.grid.place_agent(agent, pos)
                self.schedule.add(agent)

        self.datacollector.collect(self)

    def step(self):
        """
        Run one step of the model.
        """
        self.happy = 0  # Reset counter of happy agents
        self.schedule.step()
        self.similarity = round(calc_similarity(self),2)
        self.datacollector.collect(self)

        if self.happy == self.schedule.get_agent_count():
            self.running = False
