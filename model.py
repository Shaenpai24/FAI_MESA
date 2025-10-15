from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agent import SurvivorAgent, GameNodeAgent, ObstacleAgent
import random

class SurvivalModel(Model):
    def __init__(self, width=10, height=10, num_obstacles=5, steps_per_day=50, seed=None):
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.steps_per_day = steps_per_day
        self.grid = MultiGrid(width, height, torus=False)
        self.running = True
        self.agent_list = []
        self._next_id = 0

        self.current_day = 1
        self.daily_scores = []
        self.steps_today = 0
        self.total_score_history = [0]

        # Place survivor
        self.survivor = SurvivorAgent(self.next_id(), self)
        self.agent_list.append(self.survivor)
        self.grid.place_agent(self.survivor, (0, 0))

        # Place obstacles
        for _ in range(num_obstacles):
            obstacle = ObstacleAgent(self.next_id(), self)
            self.agent_list.append(obstacle)
            while True:
                x, y = self.random.randrange(self.width), self.random.randrange(self.height)
                if self.grid.is_cell_empty((x, y)):
                    self.grid.place_agent(obstacle, (x, y))
                    break

        self.start_day()

        self.datacollector = DataCollector(
            model_reporters={
                "Score": lambda m: m.survivor.score,
                "Day": lambda m: m.current_day,
                "StepsToday": lambda m: m.steps_today,
            }
        )

    def next_id(self):
        self._next_id += 1
        return self._next_id

    def start_day(self):
        self.steps_today = 0
        if self.survivor:
            self.survivor.path = []

        # Remove old game nodes and add them back to the grid
        agents_to_remove = [a for a in self.agent_list if isinstance(a, GameNodeAgent)]
        for agent in agents_to_remove:
            self.grid.remove_agent(agent)
            self.agent_list.remove(agent)

        num_games_today = self.random.choice([2, 3])
        for _ in range(num_games_today):
            difficulty = self.random.randint(1, 6)
            node = GameNodeAgent(self.next_id(), self, difficulty)
            self.agent_list.append(node)
            while True:
                x, y = self.random.randrange(self.width), self.random.randrange(self.height)
                if self.grid.is_cell_empty((x, y)):
                    self.grid.place_agent(node, (x,y))
                    break

        self.activate_random_game_node()

    def activate_random_game_node(self):
        inactive_nodes = [a for a in self.agent_list if isinstance(a, GameNodeAgent) and not a.active]
        if inactive_nodes:
            node_to_activate = self.random.choice(inactive_nodes)
            node_to_activate.active = True

    def complete_game_node(self, node, success):
        node.active = False
        if success:
            self.activate_random_game_node()

    def step(self):
        if self.steps_today >= self.steps_per_day:
            self.end_day()
            return

        # Manual agent activation
        agents_to_step = self.agent_list[:]
        self.random.shuffle(agents_to_step)
        for agent in agents_to_step:
            agent.step()

        self.steps_today += 1
        self.datacollector.collect(self)

    def end_day(self):
        self.daily_scores.append(self.survivor.score - sum(self.daily_scores))
        self.total_score_history.append(self.survivor.score)
        self.current_day += 1
        self.start_day()
